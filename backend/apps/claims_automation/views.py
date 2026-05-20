"""
ML-Powered Claims Automation API Views
Provides endpoints for claim cost estimation and automated processing
Integrates dynamic Global Pricing and Workflow Settings
"""

from rest_framework import status, viewsets
from rest_framework.decorators import api_view, action, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q, Avg, Count, Sum
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal
import pandas as pd
import random
import time

from .models import ClaimEstimate, ClaimProcessingLog
from .serializers import (
    ClaimEstimateSerializer, ClaimEstimateListSerializer,
    ClaimEstimateInputSerializer, ClaimProcessingLogSerializer,
    ClaimProcessingLogListSerializer, ClaimTriageInputSerializer,
    EstimateUpdateSerializer
)
from apps.fraud_detection.models import Claim, Policy, Vehicle, Policyholder
from ml_models.model_loader import get_model_loader
from ml_models.feature_engineering import FeatureEngineer
from system_settings.models import GlobalPricingSettings

# Initialize model loader and feature engineer (singletons — fine at module level)
model_loader = get_model_loader()
feature_engineer = FeatureEngineer()

# !! DO NOT call GlobalPricingSettings.get_solo() here at module level.
# !! It would cache the values at startup and ignore any admin changes.
# !! Always call get_solo() inside each function that needs it.


# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL WORKFLOW HELPER
# ═══════════════════════════════════════════════════════════════════════════════

def _apply_global_triage_rules(estimated_cost, fraud_score=0.0):
    """
    Standardizes triage thresholds using GlobalPricingSettings singleton.
    Called fresh each time so admin changes take effect immediately.
    """
    settings = GlobalPricingSettings.get_solo()  # always fresh

    cost = float(estimated_cost)
    f_score = float(fraud_score)

    reject_thresh = float(settings.threshold_fraud_reject)
    warning_thresh = float(settings.threshold_variance_warning)
    auto_limit = float(settings.threshold_auto_approve)
    manual_limit = float(settings.threshold_manual_review)
    high_value_limit = manual_limit * 4

    if f_score >= reject_thresh:
        return {
            'recommendation': 'REJECT',
            'action': 'REJECT',
            'priority': 'URGENT',
            'days': 21,
            'reasoning': f"High fraud probability ({f_score:.1%}) exceeds global rejection threshold."
        }
    elif f_score >= warning_thresh or cost > high_value_limit:
        return {
            'recommendation': 'DETAILED_INVESTIGATION',
            'action': 'INVESTIGATE',
            'priority': 'URGENT' if f_score >= warning_thresh else 'HIGH',
            'days': 14,
            'reasoning': (
                f"Significant risk (fraud: {f_score:.1%}) or extreme value "
                f"(${cost:,.0f}) requires detailed investigation."
            )
        }
    elif cost > manual_limit:
        return {
            'recommendation': 'DETAILED_INVESTIGATION',
            'action': 'INVESTIGATE',
            'priority': 'HIGH',
            'days': 14,
            'reasoning': f"High value claim (${cost:,.0f}) exceeds standard review limits."
        }
    elif cost > auto_limit:
        return {
            'recommendation': 'MANUAL_REVIEW',
            'action': 'REVIEW',
            'priority': 'MEDIUM',
            'days': 7,
            'reasoning': (
                f"Moderate value claim (${cost:,.0f}) exceeds auto-approve limits; "
                f"requires manual review."
            )
        }
    else:
        return {
            'recommendation': 'AUTO_APPROVE',
            'action': 'APPROVE',
            'priority': 'LOW',
            'days': 3,
            'reasoning': f"Low fraud risk and low cost (${cost:,.0f}) qualify for auto-approval."
        }


def _build_cost_breakdown(estimated_cost):
    """
    Build a cost-breakdown dict using admin-configurable ratios.
    Always fetches fresh settings so admin changes are reflected immediately.
    """
    settings = GlobalPricingSettings.get_solo()
    cost = Decimal(str(estimated_cost))
    return {
        'vehicle_damage':   float(cost * settings.ratio_vehicle_damage),
        'medical_expenses': float(cost * settings.ratio_medical_expenses),
        'legal_fees':       float(cost * settings.ratio_legal_fees),
        'other_costs':      float(cost * settings.ratio_other_costs),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# VIEWSETS
# ═══════════════════════════════════════════════════════════════════════════════

class ClaimEstimateViewSet(viewsets.ModelViewSet):
    """ViewSet for ClaimEstimate management"""
    queryset = ClaimEstimate.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return ClaimEstimateListSerializer
        return ClaimEstimateSerializer

    def get_queryset(self):
        queryset = ClaimEstimate.objects.select_related(
            'claim', 'claim__policy', 'claim__policyholder'
        )
        severity = self.request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(predicted_severity=severity)
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(triage_priority=priority)
        recommendation = self.request.query_params.get('recommendation')
        if recommendation:
            queryset = queryset.filter(processing_recommendation=recommendation)
        needs_review = self.request.query_params.get('needs_review')
        if needs_review == 'true':
            queryset = queryset.filter(
                processing_recommendation__in=['MANUAL_REVIEW', 'DETAILED_INVESTIGATION']
            )
        claim_id = self.request.query_params.get('claim_id')
        if claim_id:
            queryset = queryset.filter(claim_id=claim_id)
        return queryset.order_by('-created_at')

    @action(detail=True, methods=['post'])
    def update_actual_settlement(self, request, pk=None):
        estimate = self.get_object()
        serializer = EstimateUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        estimate.actual_settlement_amount = serializer.validated_data['actual_settlement_amount']
        estimate.reviewed_at = timezone.now()
        estimate.save()

        ClaimProcessingLog.objects.create(
            claim=estimate.claim,
            estimate=estimate,
            action_type='ESTIMATE_UPDATED',
            action_description='Actual settlement amount recorded',
            is_automated=False,
            performed_by=request.user.username,
            previous_value=str(estimate.estimated_cost),
            new_value=str(estimate.actual_settlement_amount),
            result_data={
                'variance': str(estimate.variance_percentage),
                'within_tolerance': estimate.is_within_tolerance,
                'notes': serializer.validated_data.get('notes', '')
            }
        )

        return Response({
            'message': 'Actual settlement amount updated',
            'variance_percentage': estimate.variance_percentage,
            'is_within_tolerance': estimate.is_within_tolerance,
            'prediction_accuracy': estimate.prediction_accuracy
        })


class ClaimProcessingLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for ClaimProcessingLog (read-only)"""
    queryset = ClaimProcessingLog.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return ClaimProcessingLogListSerializer
        return ClaimProcessingLogSerializer

    def get_queryset(self):
        queryset = ClaimProcessingLog.objects.select_related('claim', 'estimate')
        claim_id = self.request.query_params.get('claim_id')
        if claim_id:
            queryset = queryset.filter(claim_id=claim_id)
        estimate_id = self.request.query_params.get('estimate_id')
        if estimate_id:
            queryset = queryset.filter(estimate_id=estimate_id)
        action_type = self.request.query_params.get('action_type')
        if action_type:
            queryset = queryset.filter(action_type=action_type)
        is_automated = self.request.query_params.get('is_automated')
        if is_automated is not None:
            queryset = queryset.filter(is_automated=is_automated.lower() == 'true')
        return queryset.order_by('-created_at')


def prepare_claims_features(claim):
    policy = claim.policy
    vehicle = claim.vehicle
    claim_type_map = {
        'COLLISION': 0, 'COMPREHENSIVE': 1, 'LIABILITY': 2,
        'THEFT': 3, 'VANDALISM': 4, 'WEATHER': 5
    }
    severity_map = {'MINOR': 0, 'MODERATE': 1, 'MAJOR': 2, 'CRITICAL': 3}
    vehicle_type_map = {'Sedan': 0, 'SUV': 1, 'Truck': 2, 'Coupe': 3, 'Van': 4}
    policy_type_map = {'COMPREHENSIVE': 0, 'THIRD_PARTY': 1, 'COLLISION': 2, 'LIABILITY': 3}

    current_year = date.today().year
    vehicle_age = current_year - vehicle.manufacture_year

    features = {
        'claim_type_encoded': claim_type_map.get(claim.claim_type, 0),
        'severity_encoded': severity_map.get(claim.severity, 1),
        'vehicle_age': vehicle_age,
        'vehicle_value': float(vehicle.market_value),
        'vehicle_type_encoded': vehicle_type_map.get(vehicle.vehicle_type, 0),
        'number_of_vehicles_involved': claim.number_of_vehicles_involved,
        'coverage_amount': float(policy.coverage_amount),
        'deductible': float(policy.deductible),
        'policy_type_encoded': policy_type_map.get(policy.policy_type, 0)
    }
    return pd.DataFrame([features])


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def estimate_claim_cost(request):
    start_time = time.time()
    try:
        input_serializer = ClaimEstimateInputSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = input_serializer.validated_data
        claim_id = data['claim_id']

        try:
            claim = Claim.objects.select_related('policy', 'vehicle', 'policyholder').get(id=claim_id)
        except Claim.DoesNotExist:
            return Response({'error': 'Claim not found'}, status=status.HTTP_404_NOT_FOUND)

        existing_estimate = ClaimEstimate.objects.filter(claim=claim).first()
        if existing_estimate:
            return Response(
                {
                    'message': 'Estimate already exists for this claim',
                    'estimate_id': str(existing_estimate.id),
                    'estimate_number': existing_estimate.estimate_number
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        features_df = prepare_claims_features(claim)

        if data.get('override_severity'):
            severity_map = {'MINOR': 0, 'MODERATE': 1, 'MAJOR': 2, 'CRITICAL': 3}
            features_df['severity_encoded'] = severity_map[data['override_severity']]

        try:
            prediction = model_loader.estimate_claim_cost(features_df.iloc[0])
            estimated_cost = Decimal(str(prediction['estimated_cost']))
            lower_bound = Decimal(str(prediction['confidence_interval'][0]))
            upper_bound = Decimal(str(prediction['confidence_interval'][1]))
            severity = prediction['severity']
            recommended_reserve = Decimal(str(prediction['recommended_reserve']))
        except Exception as e:
            return Response(
                {'error': f'ML prediction failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        confidence_range = float(upper_bound - lower_bound)
        if confidence_range > 0:
            confidence_score = 1.0 - min(confidence_range / float(estimated_cost), 1.0)
        else:
            confidence_score = 0.85

        severity_choices_map = {
            'Minor': 'MINOR', 'Moderate': 'MODERATE',
            'Major': 'MAJOR', 'Critical': 'CRITICAL'
        }
        predicted_severity = severity_choices_map.get(severity, 'MODERATE')
        severity_score_map = {'MINOR': 0.25, 'MODERATE': 0.5, 'MAJOR': 0.75, 'CRITICAL': 1.0}
        severity_score = severity_score_map[predicted_severity]

        triage = _apply_global_triage_rules(estimated_cost, claim.fraud_score or 0.0)

        # Use admin-configurable ratios (not hardcoded)
        cost_breakdown = _build_cost_breakdown(estimated_cost)

        risk_factors = {
            'severity_impact': f"{predicted_severity} severity claim",
            'vehicles_involved': f"{claim.number_of_vehicles_involved} vehicles involved",
        }

        estimate_number = f"EST-{random.randint(100000000000, 999999999999)}"

        estimate = ClaimEstimate.objects.create(
            estimate_number=estimate_number,
            claim=claim,
            estimated_cost=estimated_cost,
            confidence_score=confidence_score,
            confidence_lower_bound=lower_bound,
            confidence_upper_bound=upper_bound,
            predicted_severity=predicted_severity,
            severity_score=severity_score,
            recommended_reserve=recommended_reserve,
            reserve_adequacy_ratio=float(recommended_reserve / estimated_cost),
            processing_recommendation=triage['recommendation'],
            triage_priority=triage['priority'],
            estimated_processing_days=triage['days'],
            cost_breakdown=cost_breakdown,
            risk_factors=risk_factors,
            model_version='1.0',
            features_used=list(features_df.columns),
            final_estimate=estimated_cost
        )

        processing_time = int((time.time() - start_time) * 1000)

        ClaimProcessingLog.objects.create(
            claim=claim,
            estimate=estimate,
            action_type='ESTIMATE_GENERATED',
            action_description=f'ML-based cost estimate generated: ${estimated_cost:.2f}',
            is_automated=True,
            performed_by='SYSTEM',
            result_data={
                'estimated_cost': str(estimated_cost),
                'confidence_score': confidence_score,
                'predicted_severity': predicted_severity,
                'processing_recommendation': triage['recommendation']
            },
            processing_time_ms=processing_time,
            model_version='1.0'
        )

        serializer = ClaimEstimateSerializer(estimate)
        return Response({
            'message': 'Cost estimate generated successfully',
            'estimate': serializer.data,
            'processing_time_ms': processing_time
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response(
            {'error': f'Error estimating cost: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def batch_triage_claims(request):
    try:
        input_serializer = ClaimTriageInputSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        claim_ids = input_serializer.validated_data['claim_ids']
        claims = Claim.objects.filter(id__in=claim_ids).select_related(
            'policy', 'vehicle', 'policyholder'
        )

        results = []
        for claim in claims:
            estimate = ClaimEstimate.objects.filter(claim=claim).first()
            if not estimate:
                try:
                    features_df = prepare_claims_features(claim)
                    prediction = model_loader.estimate_claim_cost(features_df.iloc[0])
                    estimated_cost = Decimal(str(prediction['estimated_cost']))
                    predicted_severity = prediction['severity']
                    triage = _apply_global_triage_rules(estimated_cost, claim.fraud_score or 0.0)
                    results.append({
                        'claim_id': str(claim.id),
                        'claim_number': claim.claim_number,
                        'estimated_cost': float(estimated_cost),
                        'triage_priority': triage['priority'],
                        'predicted_severity': predicted_severity,
                        'status': 'triaged'
                    })
                except Exception as e:
                    results.append({
                        'claim_id': str(claim.id),
                        'claim_number': claim.claim_number,
                        'status': 'error',
                        'error': str(e)
                    })
            else:
                results.append({
                    'claim_id': str(claim.id),
                    'claim_number': claim.claim_number,
                    'estimated_cost': float(estimate.estimated_cost),
                    'triage_priority': estimate.triage_priority,
                    'predicted_severity': estimate.predicted_severity,
                    'status': 'existing'
                })

        return Response({
            'message': f'Triaged {len(results)} claims',
            'results': results,
            'summary': {
                'total': len(results),
                'triaged': len([r for r in results if r['status'] == 'triaged']),
                'existing': len([r for r in results if r['status'] == 'existing']),
                'errors': len([r for r in results if r['status'] == 'error'])
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': f'Error triaging claims: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def processing_recommendations(request, claim_id):
    try:
        try:
            claim = Claim.objects.select_related('policy', 'vehicle').get(id=claim_id)
        except Claim.DoesNotExist:
            return Response({'error': 'Claim not found'}, status=status.HTTP_404_NOT_FOUND)

        estimate = ClaimEstimate.objects.filter(claim=claim).first()
        if not estimate:
            return Response(
                {
                    'message': 'No estimate found. Generate estimate first.',
                    'suggestion': f'POST /api/claims-automation/estimate-cost/ with claim_id={claim_id}'
                },
                status=status.HTTP_404_NOT_FOUND
            )

        recommendations = {
            'claim_number': claim.claim_number,
            'estimated_cost': float(estimate.estimated_cost),
            'recommended_reserve': float(estimate.recommended_reserve),
            'processing_recommendation': estimate.processing_recommendation,
            'triage_priority': estimate.triage_priority,
            'estimated_processing_days': estimate.estimated_processing_days,
            'predicted_severity': estimate.predicted_severity,
            'actions': []
        }

        if estimate.processing_recommendation == 'AUTO_APPROVE':
            recommendations['actions'].append({
                'action': 'Approve automatically',
                'reason': 'Low cost claim within global auto-approval limits',
                'priority': 'LOW'
            })
        elif estimate.processing_recommendation == 'MANUAL_REVIEW':
            recommendations['actions'].append({
                'action': 'Assign to claims adjuster',
                'reason': 'Standard claim requiring manual review',
                'priority': 'MEDIUM'
            })
        elif estimate.processing_recommendation in ['DETAILED_INVESTIGATION', 'REJECT']:
            recommendations['actions'].append({
                'action': 'Conduct detailed investigation',
                'reason': 'High value or high risk claim',
                'priority': 'HIGH'
            })
            settings = GlobalPricingSettings.get_solo()
            if claim.fraud_score and claim.fraud_score >= settings.threshold_variance_warning:
                recommendations['actions'].append({
                    'action': 'Fraud investigation required',
                    'reason': (
                        f'High fraud score ({claim.fraud_score:.2%}) exceeds '
                        f'variance warning threshold'
                    ),
                    'priority': 'URGENT'
                })

        if estimate.predicted_severity in ['MAJOR', 'CRITICAL']:
            recommendations['actions'].append({
                'action': 'Assign senior adjuster',
                'reason': f'{estimate.predicted_severity} severity claim',
                'priority': 'HIGH'
            })

        recommendations['reserve_action'] = {
            'current_reserve': 0,
            'recommended_reserve': float(estimate.recommended_reserve),
            'action': f'Set reserve to ${estimate.recommended_reserve:.2f}'
        }

        return Response(recommendations, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': f'Error generating recommendations: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def estimate_claim_cost_direct(request):
    start_time = time.time()
    try:
        data = request.data
        claim_id = data.get('claim_id')
        existing_estimate = None  # declare early so finally block can reference it

        if claim_id:
            try:
                claim = Claim.objects.select_related(
                    'policy', 'vehicle', 'policyholder'
                ).get(id=claim_id)
                existing_estimate = ClaimEstimate.objects.filter(claim=claim).first()
                if existing_estimate:
                    serializer = ClaimEstimateSerializer(existing_estimate)
                    return Response({
                        'message': 'Using existing estimate',
                        'estimated_amount': float(existing_estimate.estimated_cost),
                        'confidence_score': existing_estimate.confidence_score,
                        'predicted_severity': existing_estimate.predicted_severity,
                        'claimed_amount': float(claim.claimed_amount),
                        'estimate_id': str(existing_estimate.id),
                        'estimate_number': existing_estimate.estimate_number,
                        'full_estimate': serializer.data
                    }, status=status.HTTP_200_OK)

                features_df = prepare_claims_features(claim)
                claimed_amount = float(claim.claimed_amount)

            except Claim.DoesNotExist:
                return Response({'error': 'Claim not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            required_fields = [
                'vehicle_age_years', 'vehicle_value',
                'incident_type', 'incident_severity', 'claimed_amount'
            ]
            missing_fields = [f for f in required_fields if f not in data]
            if missing_fields:
                return Response(
                    {'error': f'Missing required fields: {", ".join(missing_fields)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            claim_type_map = {
                'Collision': 0, 'Theft': 3, 'Fire': 5,
                'Vandalism': 4, 'Natural Disaster': 5, 'Other': 1
            }
            severity_map = {
                'Trivial Damage': 0, 'Minor Damage': 0,
                'Major Damage': 2, 'Total Loss': 3
            }
            features = {
                'claim_type_encoded': claim_type_map.get(data['incident_type'], 0),
                'severity_encoded': severity_map.get(data['incident_severity'], 1),
                'vehicle_age': int(data['vehicle_age_years']),
                'vehicle_value': float(data['vehicle_value']),
                'vehicle_type_encoded': 0,
                'number_of_vehicles_involved': 1,
                'coverage_amount': float(data['vehicle_value']) * 0.8,
                'deductible': 500.0,
                'policy_type_encoded': 0
            }
            features_df = pd.DataFrame([features])
            claimed_amount = float(data['claimed_amount'])

        # Fetch settings fresh — picks up any admin changes immediately
        settings = GlobalPricingSettings.get_solo()
        labor_rate = float(settings.labor_rate_per_hour)
        complexity_map = {'Low': 0.8, 'Medium': 1.0, 'High': 1.3}
        parts_map = {'Available': 1.0, 'Limited': 1.2, 'Rare': 1.5}

        try:
            prediction = model_loader.estimate_claim_cost(features_df.iloc[0])
            estimated_amount = float(prediction['estimated_cost'])

            if not claim_id:
                complexity_multiplier = complexity_map.get(
                    data.get('repair_complexity', 'Medium'), 1.0
                )
                parts_multiplier = parts_map.get(
                    data.get('parts_availability', 'Available'), 1.0
                )
                labor_hours = int(data.get('labor_hours_estimate', 20))
                labor_cost = labor_hours * labor_rate
                estimated_amount = (
                    (estimated_amount * complexity_multiplier * parts_multiplier)
                    + (labor_cost * 0.3)
                )

            confidence_score = 0.85
            severity = prediction['severity']

        except Exception as e:
            print(f"ML prediction failed: {e}, using fallback estimation")
            if not claim_id:
                # Use admin-configurable severity multipliers for fallback too
                severity_multipliers = {
                    'Trivial Damage': float(settings.sev_trivial_mult),
                    'Minor Damage':   float(settings.sev_minor_mult),
                    'Major Damage':   float(settings.sev_major_mult),
                    'Total Loss':     float(settings.sev_total_mult),
                }
                base_estimate = (
                    float(data['vehicle_value'])
                    * severity_multipliers.get(data['incident_severity'], 0.25)
                )
                labor_hours = int(data.get('labor_hours_estimate', 20))
                labor_cost = labor_hours * labor_rate
                complexity_adj = complexity_map.get(
                    data.get('repair_complexity', 'Medium'), 1.0
                )
                parts_adj = parts_map.get(
                    data.get('parts_availability', 'Available'), 1.0
                )
                estimated_amount = (base_estimate + labor_cost) * complexity_adj * parts_adj
                severity = data['incident_severity']
            else:
                estimated_amount = float(claim.vehicle.market_value) * 0.25
                severity = 'Moderate'
            confidence_score = 0.70

        severity_map_response = {
            'Minor': 'Minor Damage', 'Moderate': 'Major Damage',
            'Major': 'Major Damage', 'Critical': 'Total Loss'
        }
        predicted_severity = severity_map_response.get(severity, severity)

        fraud_val = claim.fraud_score if claim_id else 0.0
        triage = _apply_global_triage_rules(estimated_amount, fraud_val)

        variance = abs(estimated_amount - claimed_amount)
        variance_percentage = (variance / claimed_amount * 100) if claimed_amount > 0 else 0
        processing_time = int((time.time() - start_time) * 1000)

        # Use admin-configurable cost-breakdown ratios (not hardcoded 0.5 / 0.3 / 0.2)
        est_dec = Decimal(str(estimated_amount))
        cost_breakdown = {
            'vehicle_damage':   round(float(est_dec * settings.ratio_vehicle_damage), 2),
            'medical_expenses': round(float(est_dec * settings.ratio_medical_expenses), 2),
            'legal_fees':       round(float(est_dec * settings.ratio_legal_fees), 2),
            'other_costs':      round(float(est_dec * settings.ratio_other_costs), 2),
        }

        response_data = {
            'estimated_amount': round(estimated_amount, 2),
            'confidence_score': round(confidence_score, 2),
            'predicted_severity': predicted_severity,
            'claimed_amount': claimed_amount,
            'variance': round(variance, 2),
            'variance_percentage': round(variance_percentage, 2),
            'processing_time_ms': processing_time,
            'recommendation': triage['recommendation'],
            'priority': triage['priority'],
            'is_new_estimate': claim_id is None,
            'cost_breakdown': cost_breakdown,
        }

        if claim_id and not existing_estimate:
            response_data['message'] = (
                'Estimate calculated (not saved). '
                'Use POST to /estimates/ to save.'
            )

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': f'Error estimating cost: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def claims_statistics(request):
    try:
        total_estimates = ClaimEstimate.objects.count()
        by_severity = {}
        for severity in ['MINOR', 'MODERATE', 'MAJOR', 'CRITICAL']:
            count = ClaimEstimate.objects.filter(predicted_severity=severity).count()
            avg_cost = (
                ClaimEstimate.objects.filter(predicted_severity=severity)
                .aggregate(Avg('estimated_cost'))['estimated_cost__avg'] or 0
            )
            by_severity[severity] = {'count': count, 'avg_cost': float(avg_cost)}

        by_priority = {
            p: ClaimEstimate.objects.filter(triage_priority=p).count()
            for p in ['LOW', 'MEDIUM', 'HIGH', 'URGENT']
        }
        by_recommendation = {
            r: ClaimEstimate.objects.filter(processing_recommendation=r).count()
            for r in ['AUTO_APPROVE', 'MANUAL_REVIEW', 'DETAILED_INVESTIGATION', 'REJECT']
        }

        estimates_with_actual = ClaimEstimate.objects.exclude(
            actual_settlement_amount__isnull=True
        )
        accuracy_stats = {
            'total_validated': estimates_with_actual.count(),
            'avg_accuracy': float(
                estimates_with_actual.aggregate(Avg('prediction_accuracy'))
                ['prediction_accuracy__avg'] or 0
            ),
            'within_tolerance': estimates_with_actual.filter(
                prediction_accuracy__gte=80
            ).count()
        }

        total_logs = ClaimProcessingLog.objects.count()
        automated_logs = ClaimProcessingLog.objects.filter(is_automated=True).count()
        avg_estimated_cost = (
            ClaimEstimate.objects.aggregate(Avg('estimated_cost'))['estimated_cost__avg'] or 0
        )
        avg_reserve = (
            ClaimEstimate.objects.aggregate(Avg('recommended_reserve'))
            ['recommended_reserve__avg'] or 0
        )

        return Response({
            'total_estimates': total_estimates,
            'by_severity': by_severity,
            'by_priority': by_priority,
            'by_recommendation': by_recommendation,
            'accuracy_statistics': accuracy_stats,
            'processing_logs': {
                'total': total_logs,
                'automated': automated_logs,
                'manual': total_logs - automated_logs
            },
            'average_costs': {
                'estimated_cost': float(avg_estimated_cost),
                'recommended_reserve': float(avg_reserve)
            },
            'generated_at': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': f'Error generating statistics: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def auto_process_claim(request, claim_id):
    start_time = time.time()
    try:
        try:
            claim = Claim.objects.select_related(
                'policy', 'vehicle', 'policyholder'
            ).get(id=claim_id)
        except Claim.DoesNotExist:
            return Response({'error': 'Claim not found'}, status=status.HTTP_404_NOT_FOUND)

        from apps.fraud_detection.ml_views import _analyze_existing_claim
        fraud_response = _analyze_existing_claim(str(claim_id))
        if fraud_response.status_code != 200:
            return Response(
                {'error': 'Fraud analysis failed', 'details': fraud_response.data},
                status=fraud_response.status_code
            )

        fraud_data = fraud_response.data
        fraud_score = float(fraud_data.get('fraud_score', 0))
        estimate_data = {}
        estimate = ClaimEstimate.objects.filter(claim=claim).first()

        try:
            if not estimate:
                features_df = prepare_claims_features(claim)
                prediction = model_loader.estimate_claim_cost(features_df.iloc[0])

                estimated_cost = Decimal(str(prediction['estimated_cost']))
                lower_bound = Decimal(str(prediction['confidence_interval'][0]))
                upper_bound = Decimal(str(prediction['confidence_interval'][1]))
                severity = prediction['severity']
                recommended_reserve = Decimal(str(prediction['recommended_reserve']))

                confidence_range = float(upper_bound - lower_bound)
                confidence_score = (
                    1.0 - min(confidence_range / float(estimated_cost), 1.0)
                    if confidence_range > 0 else 0.85
                )

                severity_choices_map = {
                    'Minor': 'MINOR', 'Moderate': 'MODERATE',
                    'Major': 'MAJOR', 'Critical': 'CRITICAL'
                }
                predicted_severity = severity_choices_map.get(severity, 'MODERATE')
                triage = _apply_global_triage_rules(estimated_cost, fraud_score)

                # Use admin-configurable ratios — not hardcoded Decimal literals
                cost_breakdown = _build_cost_breakdown(estimated_cost)

                estimate_number = f"EST-{random.randint(100000000000, 999999999999)}"
                estimate = ClaimEstimate.objects.create(
                    estimate_number=estimate_number,
                    claim=claim,
                    estimated_cost=estimated_cost,
                    confidence_score=confidence_score,
                    confidence_lower_bound=lower_bound,
                    confidence_upper_bound=upper_bound,
                    predicted_severity=predicted_severity,
                    severity_score={
                        'MINOR': 0.25, 'MODERATE': 0.5,
                        'MAJOR': 0.75, 'CRITICAL': 1.0
                    }[predicted_severity],
                    recommended_reserve=recommended_reserve,
                    reserve_adequacy_ratio=float(recommended_reserve / estimated_cost),
                    processing_recommendation=triage['recommendation'],
                    triage_priority=triage['priority'],
                    estimated_processing_days=triage['days'],
                    cost_breakdown=cost_breakdown,
                    risk_factors={
                        'fraud_score': fraud_score,
                        'severity_impact': f"{predicted_severity} severity claim",
                        'cost_estimate': f"${estimated_cost:,.2f}"
                    },
                    model_version='1.0',
                    features_used=list(features_df.columns),
                    final_estimate=estimated_cost
                )

            estimate_serializer = ClaimEstimateSerializer(estimate)
            estimate_data = estimate_serializer.data

        except Exception as e:
            print(f"Cost estimation failed: {e}")
            estimate_data = {'error': 'Cost estimation unavailable', 'message': str(e)}

        estimated_cost = (
            float(estimate.estimated_cost) if estimate else float(claim.claimed_amount)
        )
        global_triage = _apply_global_triage_rules(estimated_cost, fraud_score)

        # Fetch settings once here for the action_items checks
        settings = GlobalPricingSettings.get_solo()
        action_items = []
        if fraud_score >= float(settings.threshold_fraud_reject):
            action_items.append({
                'action': 'Fraud Investigation',
                'priority': 'URGENT',
                'reason': f'High fraud score: {fraud_score:.1%}'
            })
        if estimated_cost >= float(settings.threshold_manual_review):
            action_items.append({
                'action': 'Senior Adjuster Review',
                'priority': 'HIGH',
                'reason': f'High value claim: ${estimated_cost:,.0f}'
            })

        processing_time = int((time.time() - start_time) * 1000)

        ClaimProcessingLog.objects.create(
            claim=claim,
            estimate=estimate,
            action_type='AUTO_PROCESS',
            action_description=(
                f'Automated claim processing: {global_triage["recommendation"]}'
            ),
            is_automated=True,
            performed_by='SYSTEM',
            result_data={
                'fraud_score': fraud_score,
                'estimated_cost': str(estimated_cost),
                'recommendation': global_triage["recommendation"],
                'priority': global_triage["priority"]
            },
            processing_time_ms=processing_time,
            model_version='1.0'
        )

        return Response({
            'claim_id': str(claim.id),
            'claim_number': claim.claim_number,
            'processing_summary': {
                'recommendation': global_triage['recommendation'],
                'action': global_triage['action'],
                'priority': global_triage['priority'],
                'reasoning': global_triage['reasoning'],
                'confidence': (
                    'HIGH' if fraud_score > 0.7 or fraud_score < 0.3 else 'MEDIUM'
                )
            },
            'fraud_analysis': {
                'fraud_score': fraud_score,
                'is_fraudulent': fraud_data.get('is_fraudulent'),
                'risk_level': fraud_data.get('fraud_analysis', {}).get('risk_level'),
                'risk_factors': fraud_data.get('risk_factors', [])
            },
            'cost_estimation': {
                'estimated_cost': estimated_cost,
                'claimed_amount': float(claim.claimed_amount),
                'variance': abs(estimated_cost - float(claim.claimed_amount)),
                'confidence_score': estimate.confidence_score if estimate else None,
                'predicted_severity': estimate.predicted_severity if estimate else None,
                'recommended_reserve': (
                    float(estimate.recommended_reserve) if estimate else None
                )
            },
            'action_items': action_items,
            'next_steps': {
                'immediate': global_triage['action'],
                'estimated_days': (
                    estimate.estimated_processing_days if estimate else None
                ),
                'assigned_priority': global_triage['priority']
            },
            'processing_metadata': {
                'processed_at': timezone.now().isoformat(),
                'processing_time_ms': processing_time,
                'model_version': '1.0',
                'automated': True
            },
            'detailed_fraud_analysis': fraud_data,
            'detailed_estimate': estimate_data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': f'Error processing claim: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )