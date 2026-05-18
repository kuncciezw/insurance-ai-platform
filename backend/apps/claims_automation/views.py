"""
ML-Powered Claims Automation API Views
Provides endpoints for claim cost estimation and automated processing
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


# Initialize model loader and feature engineer
model_loader = get_model_loader()
feature_engineer = FeatureEngineer()


class ClaimEstimateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ClaimEstimate management

    List, create, retrieve, update, and delete claim estimates
    """
    queryset = ClaimEstimate.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return ClaimEstimateListSerializer
        return ClaimEstimateSerializer

    def get_queryset(self):
        """Filter estimates with query parameters"""
        queryset = ClaimEstimate.objects.select_related(
            'claim', 'claim__policy', 'claim__policyholder'
        )

        # Filter by severity
        severity = self.request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(predicted_severity=severity)

        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(triage_priority=priority)

        # Filter by recommendation
        recommendation = self.request.query_params.get('recommendation')
        if recommendation:
            queryset = queryset.filter(processing_recommendation=recommendation)

        # Filter needs review
        needs_review = self.request.query_params.get('needs_review')
        if needs_review == 'true':
            queryset = queryset.filter(
                processing_recommendation__in=['MANUAL_REVIEW', 'DETAILED_INVESTIGATION']
            )

        # Filter by claim
        claim_id = self.request.query_params.get('claim_id')
        if claim_id:
            queryset = queryset.filter(claim_id=claim_id)

        return queryset.order_by('-created_at')

    @action(detail=True, methods=['post'])
    def update_actual_settlement(self, request, pk=None):
        """Update estimate with actual settlement amount"""
        estimate = self.get_object()

        serializer = EstimateUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        estimate.actual_settlement_amount = serializer.validated_data['actual_settlement_amount']
        estimate.reviewed_at = timezone.now()
        estimate.save()

        # Create log entry
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
    """
    ViewSet for ClaimProcessingLog (read-only)

    View automated processing history for claims
    """
    queryset = ClaimProcessingLog.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return ClaimProcessingLogListSerializer
        return ClaimProcessingLogSerializer

    def get_queryset(self):
        """Filter logs with query parameters"""
        queryset = ClaimProcessingLog.objects.select_related(
            'claim', 'estimate'
        )

        # Filter by claim
        claim_id = self.request.query_params.get('claim_id')
        if claim_id:
            queryset = queryset.filter(claim_id=claim_id)

        # Filter by estimate
        estimate_id = self.request.query_params.get('estimate_id')
        if estimate_id:
            queryset = queryset.filter(estimate_id=estimate_id)

        # Filter by action type
        action_type = self.request.query_params.get('action_type')
        if action_type:
            queryset = queryset.filter(action_type=action_type)

        # Filter automated vs manual
        is_automated = self.request.query_params.get('is_automated')
        if is_automated is not None:
            queryset = queryset.filter(is_automated=is_automated.lower() == 'true')

        return queryset.order_by('-created_at')


def prepare_claims_features(claim):
    """Prepare features for ML claims estimation model"""

    policy = claim.policy
    vehicle = claim.vehicle

    claim_type_map = {
        'COLLISION': 0, 'COMPREHENSIVE': 1, 'LIABILITY': 2,
        'THEFT': 3, 'VANDALISM': 4, 'WEATHER': 5
    }
    severity_map = {
        'MINOR': 0, 'MODERATE': 1, 'MAJOR': 2, 'CRITICAL': 3
    }
    vehicle_type_map = {
        'Sedan': 0, 'SUV': 1, 'Truck': 2, 'Coupe': 3, 'Van': 4
    }
    policy_type_map = {
        'COMPREHENSIVE': 0, 'THIRD_PARTY': 1, 'COLLISION': 2, 'LIABILITY': 3
    }

    # UPDATED: vehicle.year → vehicle.manufacture_year
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
        # DROPPED: number_of_injuries, third_party_involved, police_report_filed
        #          — these fields were removed from the Claim model
    }

    return pd.DataFrame([features])


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def estimate_claim_cost(request):
    """
    Estimate claim settlement cost using ML model

    POST /api/claims-automation/estimate-cost/
    """

    start_time = time.time()

    try:
        # Validate input
        input_serializer = ClaimEstimateInputSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response(
                input_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        data = input_serializer.validated_data
        claim_id = data['claim_id']

        # Get claim
        try:
            claim = Claim.objects.select_related(
                'policy', 'vehicle', 'policyholder'
            ).get(id=claim_id)
        except Claim.DoesNotExist:
            return Response(
                {'error': 'Claim not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if estimate already exists
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

        # Prepare features
        features_df = prepare_claims_features(claim)

        # Apply overrides if provided (for what-if analysis)
        if data.get('override_severity'):
            severity_map = {'MINOR': 0, 'MODERATE': 1, 'MAJOR': 2, 'CRITICAL': 3}
            features_df['severity_encoded'] = severity_map[data['override_severity']]
        # DROPPED: override_injuries and override_vehicles — fields removed from Claim model

        # Get ML prediction
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

        # Calculate confidence score
        confidence_range = float(upper_bound - lower_bound)
        if confidence_range > 0:
            confidence_score = 1.0 - min(confidence_range / float(estimated_cost), 1.0)
        else:
            confidence_score = 0.85

        # Map severity to choices
        severity_choices_map = {
            'Minor': 'MINOR', 'Moderate': 'MODERATE',
            'Major': 'MAJOR', 'Critical': 'CRITICAL'
        }
        predicted_severity = severity_choices_map.get(severity, 'MODERATE')

        # Calculate severity score
        severity_score_map = {
            'MINOR': 0.25, 'MODERATE': 0.5, 'MAJOR': 0.75, 'CRITICAL': 1.0
        }
        severity_score = severity_score_map[predicted_severity]

        # Determine processing recommendation
        if estimated_cost < 1000:
            processing_recommendation = 'AUTO_APPROVE'
            triage_priority = 'LOW'
            estimated_days = 3
        elif estimated_cost < 5000:
            processing_recommendation = 'MANUAL_REVIEW'
            triage_priority = 'MEDIUM'
            estimated_days = 7
        elif estimated_cost < 20000:
            processing_recommendation = 'DETAILED_INVESTIGATION'
            triage_priority = 'HIGH'
            estimated_days = 14
        else:
            processing_recommendation = 'DETAILED_INVESTIGATION'
            triage_priority = 'URGENT'
            estimated_days = 21

        # If fraud score is high, override recommendation
        if claim.fraud_score and claim.fraud_score > 0.7:
            processing_recommendation = 'DETAILED_INVESTIGATION'
            triage_priority = 'URGENT'

        # Build cost breakdown
        cost_breakdown = {
            'vehicle_damage': float(estimated_cost * Decimal('0.6')),
            'medical_expenses': float(estimated_cost * Decimal('0.2')),
            'legal_fees': float(estimated_cost * Decimal('0.1')),
            'other_costs': float(estimated_cost * Decimal('0.1'))
        }

        # Build risk factors
        # DROPPED: injury_count, third_party, police_report — fields removed from Claim model
        risk_factors = {
            'severity_impact': f"{predicted_severity} severity claim",
            'vehicles_involved': f"{claim.number_of_vehicles_involved} vehicles involved",
        }

        # Generate estimate number
        estimate_number = f"EST-{random.randint(100000000000, 999999999999)}"

        # Create estimate
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
            processing_recommendation=processing_recommendation,
            triage_priority=triage_priority,
            estimated_processing_days=estimated_days,
            cost_breakdown=cost_breakdown,
            risk_factors=risk_factors,
            model_version='1.0',
            features_used=list(features_df.columns),
            final_estimate=estimated_cost
        )

        # Calculate processing time
        processing_time = int((time.time() - start_time) * 1000)

        # Create processing log
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
                'processing_recommendation': processing_recommendation
            },
            processing_time_ms=processing_time,
            model_version='1.0'
        )

        # Serialize response
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
    """
    Automatically triage multiple claims based on ML estimates

    POST /api/claims-automation/batch-triage/
    """

    try:
        # Validate input
        input_serializer = ClaimTriageInputSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response(
                input_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        claim_ids = input_serializer.validated_data['claim_ids']

        # Get claims
        claims = Claim.objects.filter(id__in=claim_ids).select_related(
            'policy', 'vehicle', 'policyholder'
        )

        results = []

        for claim in claims:
            # Check if estimate exists
            estimate = ClaimEstimate.objects.filter(claim=claim).first()

            if not estimate:
                # Generate estimate if doesn't exist
                try:
                    features_df = prepare_claims_features(claim)
                    prediction = model_loader.estimate_claim_cost(features_df.iloc[0])

                    estimated_cost = Decimal(str(prediction['estimated_cost']))
                    predicted_severity = prediction['severity']

                    # Determine triage
                    if estimated_cost < 1000:
                        triage_priority = 'LOW'
                    elif estimated_cost < 5000:
                        triage_priority = 'MEDIUM'
                    elif estimated_cost < 20000:
                        triage_priority = 'HIGH'
                    else:
                        triage_priority = 'URGENT'

                    results.append({
                        'claim_id': str(claim.id),
                        'claim_number': claim.claim_number,
                        'estimated_cost': float(estimated_cost),
                        'triage_priority': triage_priority,
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
    """
    Get automated processing recommendations for a claim

    GET /api/claims-automation/recommendations/<claim_id>/
    """

    try:
        # Get claim
        try:
            claim = Claim.objects.select_related('policy', 'vehicle').get(id=claim_id)
        except Claim.DoesNotExist:
            return Response(
                {'error': 'Claim not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get or create estimate
        estimate = ClaimEstimate.objects.filter(claim=claim).first()

        if not estimate:
            return Response(
                {
                    'message': 'No estimate found. Generate estimate first.',
                    'suggestion': f'POST /api/claims-automation/estimate-cost/ with claim_id={claim_id}'
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # Build recommendations
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

        # Generate specific actions
        if estimate.processing_recommendation == 'AUTO_APPROVE':
            recommendations['actions'].append({
                'action': 'Approve automatically',
                'reason': 'Low cost claim within auto-approval limits',
                'priority': 'LOW'
            })

        if estimate.processing_recommendation == 'MANUAL_REVIEW':
            recommendations['actions'].append({
                'action': 'Assign to claims adjuster',
                'reason': 'Standard claim requiring manual review',
                'priority': 'MEDIUM'
            })

        if estimate.processing_recommendation == 'DETAILED_INVESTIGATION':
            recommendations['actions'].append({
                'action': 'Conduct detailed investigation',
                'reason': 'High value or high risk claim',
                'priority': 'HIGH'
            })

            if claim.fraud_score and claim.fraud_score > 0.6:
                recommendations['actions'].append({
                    'action': 'Fraud investigation required',
                    'reason': f'High fraud score: {claim.fraud_score:.2%}',
                    'priority': 'URGENT'
                })

        if estimate.predicted_severity in ['MAJOR', 'CRITICAL']:
            recommendations['actions'].append({
                'action': 'Assign senior adjuster',
                'reason': f'{estimate.predicted_severity} severity claim',
                'priority': 'HIGH'
            })

        # DROPPED: if claim.number_of_injuries > 0 — field removed from Claim model
        # DROPPED: if not claim.police_report_filed — field removed from Claim model

        # Add reserve recommendation
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
    """
    Estimate claim cost - supports both direct input and existing claims

    POST /api/claims-automation/estimate-cost-direct/

    For new claims: send form data directly
    For existing claims: send claim_id
    """

    start_time = time.time()

    try:
        data = request.data
        claim_id = data.get('claim_id')

        # MODE 1: Existing claim - fetch from database
        if claim_id:
            try:
                claim = Claim.objects.select_related(
                    'policy', 'vehicle', 'policyholder'
                ).get(id=claim_id)

                # Check if estimate already exists
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

                # Prepare features from existing claim
                features_df = prepare_claims_features(claim)
                claimed_amount = float(claim.claimed_amount)

            except Claim.DoesNotExist:
                return Response(
                    {'error': 'Claim not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

        # MODE 2: New claim - use form data directly
        else:
            # Validate required fields for direct estimation
            required_fields = [
                'vehicle_age_years', 'vehicle_value', 'incident_type',
                'incident_severity', 'claimed_amount'
            ]

            missing_fields = [f for f in required_fields if f not in data]
            if missing_fields:
                return Response(
                    {'error': f'Missing required fields: {", ".join(missing_fields)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Map frontend fields to ML model features
            claim_type_map = {
                'Collision': 0, 'Theft': 3, 'Fire': 5,
                'Vandalism': 4, 'Natural Disaster': 5, 'Other': 1
            }

            severity_map = {
                'Trivial Damage': 0, 'Minor Damage': 0,
                'Major Damage': 2, 'Total Loss': 3
            }

            complexity_map = {
                'Low': 0.8, 'Medium': 1.0, 'High': 1.3
            }

            parts_map = {
                'Available': 1.0, 'Limited': 1.2, 'Rare': 1.5
            }

            # Create features dictionary
            # DROPPED: number_of_injuries, third_party_involved, police_report_filed
            #          — fields removed from the Claim model
            features = {
                'claim_type_encoded': claim_type_map.get(data['incident_type'], 0),
                'severity_encoded': severity_map.get(data['incident_severity'], 1),
                'vehicle_age': int(data['vehicle_age_years']),
                'vehicle_value': float(data['vehicle_value']),
                'vehicle_type_encoded': 0,  # Default
                'number_of_vehicles_involved': 1,
                'coverage_amount': float(data['vehicle_value']) * 0.8,
                'deductible': 500.0,
                'policy_type_encoded': 0
            }

            features_df = pd.DataFrame([features])
            claimed_amount = float(data['claimed_amount'])

        # Get ML prediction
        try:
            prediction = model_loader.estimate_claim_cost(features_df.iloc[0])
            estimated_amount = float(prediction['estimated_cost'])

            # Apply adjustments for direct estimation (new claims)
            if not claim_id:
                complexity_multiplier = complexity_map.get(
                    data.get('repair_complexity', 'Medium'), 1.0
                )
                parts_multiplier = parts_map.get(
                    data.get('parts_availability', 'Available'), 1.0
                )
                labor_hours = int(data.get('labor_hours_estimate', 20))
                labor_cost = labor_hours * 75  # $75/hour average

                estimated_amount = (
                    estimated_amount * complexity_multiplier * parts_multiplier
                ) + (labor_cost * 0.3)

            confidence_score = 0.85
            severity = prediction['severity']

        except Exception as e:
            # Fallback to rule-based estimation if ML fails
            print(f"ML prediction failed: {e}, using fallback estimation")

            if not claim_id:
                severity_multipliers = {
                    'Trivial Damage': 0.05,
                    'Minor Damage': 0.15,
                    'Major Damage': 0.35,
                    'Total Loss': 1.0
                }

                base_estimate = float(data['vehicle_value']) * severity_multipliers.get(
                    data['incident_severity'], 0.25
                )

                labor_hours = int(data.get('labor_hours_estimate', 20))
                labor_cost = labor_hours * 75

                complexity_adj = complexity_map.get(data.get('repair_complexity', 'Medium'), 1.0)
                parts_adj = parts_map.get(data.get('parts_availability', 'Available'), 1.0)

                estimated_amount = (base_estimate + labor_cost) * complexity_adj * parts_adj
                severity = data['incident_severity']

            else:
                estimated_amount = float(claim.vehicle.market_value) * 0.25
                severity = 'Moderate'

            confidence_score = 0.70

        # Map severity for response
        severity_map_response = {
            'Minor': 'Minor Damage',
            'Moderate': 'Major Damage',
            'Major': 'Major Damage',
            'Critical': 'Total Loss'
        }
        predicted_severity = severity_map_response.get(severity, severity)

        # Determine recommendation
        if estimated_amount < 1000:
            recommendation = 'AUTO_APPROVE'
            priority = 'LOW'
        elif estimated_amount < 5000:
            recommendation = 'MANUAL_REVIEW'
            priority = 'MEDIUM'
        elif estimated_amount < 20000:
            recommendation = 'DETAILED_INVESTIGATION'
            priority = 'HIGH'
        else:
            recommendation = 'DETAILED_INVESTIGATION'
            priority = 'URGENT'

        # Calculate variance
        variance = abs(estimated_amount - claimed_amount)
        variance_percentage = (variance / claimed_amount * 100) if claimed_amount > 0 else 0

        # Calculate processing time
        processing_time = int((time.time() - start_time) * 1000)

        # Build response
        response_data = {
            'estimated_amount': round(estimated_amount, 2),
            'confidence_score': round(confidence_score, 2),
            'predicted_severity': predicted_severity,
            'claimed_amount': claimed_amount,
            'variance': round(variance, 2),
            'variance_percentage': round(variance_percentage, 2),
            'processing_time_ms': processing_time,
            'recommendation': recommendation,
            'priority': priority,
            'is_new_estimate': claim_id is None,
            'cost_breakdown': {
                'parts': round(estimated_amount * 0.5, 2),
                'labor': round(estimated_amount * 0.3, 2),
                'other': round(estimated_amount * 0.2, 2)
            }
        }

        if claim_id and not existing_estimate:
            response_data['message'] = 'Estimate calculated (not saved). Use POST to /estimates/ to save.'

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        import traceback
        print(f"Error in estimate_claim_cost_direct: {str(e)}")
        print(traceback.format_exc())
        return Response(
            {'error': f'Error estimating cost: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def claims_statistics(request):
    """
    Get claims automation statistics

    GET /api/claims-automation/statistics/
    """

    try:
        total_estimates = ClaimEstimate.objects.count()

        # By severity
        by_severity = {}
        for severity in ['MINOR', 'MODERATE', 'MAJOR', 'CRITICAL']:
            count = ClaimEstimate.objects.filter(predicted_severity=severity).count()
            avg_cost = ClaimEstimate.objects.filter(
                predicted_severity=severity
            ).aggregate(Avg('estimated_cost'))['estimated_cost__avg'] or 0

            by_severity[severity] = {
                'count': count,
                'avg_cost': float(avg_cost)
            }

        # By priority
        by_priority = {}
        for priority in ['LOW', 'MEDIUM', 'HIGH', 'URGENT']:
            count = ClaimEstimate.objects.filter(triage_priority=priority).count()
            by_priority[priority] = count

        # By recommendation
        by_recommendation = {}
        for rec in ['AUTO_APPROVE', 'MANUAL_REVIEW', 'DETAILED_INVESTIGATION', 'REJECT']:
            count = ClaimEstimate.objects.filter(processing_recommendation=rec).count()
            by_recommendation[rec] = count

        # Accuracy statistics
        estimates_with_actual = ClaimEstimate.objects.exclude(
            actual_settlement_amount__isnull=True
        )

        accuracy_stats = {
            'total_validated': estimates_with_actual.count(),
            'avg_accuracy': float(
                estimates_with_actual.aggregate(
                    Avg('prediction_accuracy')
                )['prediction_accuracy__avg'] or 0
            ),
            'within_tolerance': estimates_with_actual.filter(
                prediction_accuracy__gte=80
            ).count()
        }

        # Processing logs
        total_logs = ClaimProcessingLog.objects.count()
        automated_logs = ClaimProcessingLog.objects.filter(is_automated=True).count()

        avg_estimated_cost = ClaimEstimate.objects.aggregate(
            Avg('estimated_cost')
        )['estimated_cost__avg'] or 0

        avg_reserve = ClaimEstimate.objects.aggregate(
            Avg('recommended_reserve')
        )['recommended_reserve__avg'] or 0

        response_data = {
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
        }

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': f'Error generating statistics: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def auto_process_claim(request, claim_id):
    """
    Automatically process a claim with both fraud detection and cost estimation

    POST /api/claims-automation/claims/<claim_id>/auto-process/
    """

    start_time = time.time()

    try:
        # Get the claim
        try:
            claim = Claim.objects.select_related(
                'policy', 'vehicle', 'policyholder'
            ).get(id=claim_id)
        except Claim.DoesNotExist:
            return Response(
                {'error': 'Claim not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # STEP 1: Fraud Detection Analysis
        from apps.fraud_detection.ml_views import _analyze_existing_claim

        fraud_response = _analyze_existing_claim(str(claim_id))

        if fraud_response.status_code != 200:
            return Response(
                {'error': 'Fraud analysis failed', 'details': fraud_response.data},
                status=fraud_response.status_code
            )

        fraud_data = fraud_response.data

        # STEP 2: Cost Estimation
        estimate = None
        estimate_data = {}

        try:
            estimate = ClaimEstimate.objects.filter(claim=claim).first()

            if not estimate:
                features_df = prepare_claims_features(claim)
                prediction = model_loader.estimate_claim_cost(features_df.iloc[0])

                estimated_cost = Decimal(str(prediction['estimated_cost']))
                lower_bound = Decimal(str(prediction['confidence_interval'][0]))
                upper_bound = Decimal(str(prediction['confidence_interval'][1]))
                severity = prediction['severity']
                recommended_reserve = Decimal(str(prediction['recommended_reserve']))

                confidence_range = float(upper_bound - lower_bound)
                confidence_score = 1.0 - min(confidence_range / float(estimated_cost), 1.0) if confidence_range > 0 else 0.85

                severity_choices_map = {
                    'Minor': 'MINOR', 'Moderate': 'MODERATE',
                    'Major': 'MAJOR', 'Critical': 'CRITICAL'
                }
                predicted_severity = severity_choices_map.get(severity, 'MODERATE')

                fraud_score = float(fraud_data.get('fraud_score', 0))

                if fraud_score >= 0.8 or estimated_cost > 50000:
                    processing_recommendation = 'DETAILED_INVESTIGATION'
                    triage_priority = 'URGENT'
                    estimated_days = 21
                elif fraud_score >= 0.6 or estimated_cost > 20000:
                    processing_recommendation = 'DETAILED_INVESTIGATION'
                    triage_priority = 'HIGH'
                    estimated_days = 14
                elif fraud_score >= 0.4 or estimated_cost > 5000:
                    processing_recommendation = 'MANUAL_REVIEW'
                    triage_priority = 'MEDIUM'
                    estimated_days = 7
                else:
                    processing_recommendation = 'AUTO_APPROVE'
                    triage_priority = 'LOW'
                    estimated_days = 3

                estimate_number = f"EST-{random.randint(100000000000, 999999999999)}"

                estimate = ClaimEstimate.objects.create(
                    estimate_number=estimate_number,
                    claim=claim,
                    estimated_cost=estimated_cost,
                    confidence_score=confidence_score,
                    confidence_lower_bound=lower_bound,
                    confidence_upper_bound=upper_bound,
                    predicted_severity=predicted_severity,
                    severity_score={'MINOR': 0.25, 'MODERATE': 0.5, 'MAJOR': 0.75, 'CRITICAL': 1.0}[predicted_severity],
                    recommended_reserve=recommended_reserve,
                    reserve_adequacy_ratio=float(recommended_reserve / estimated_cost),
                    processing_recommendation=processing_recommendation,
                    triage_priority=triage_priority,
                    estimated_processing_days=estimated_days,
                    cost_breakdown={
                        'vehicle_damage': float(estimated_cost * Decimal('0.6')),
                        'medical_expenses': float(estimated_cost * Decimal('0.2')),
                        'legal_fees': float(estimated_cost * Decimal('0.1')),
                        'other_costs': float(estimated_cost * Decimal('0.1'))
                    },
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
            estimate_data = {
                'error': 'Cost estimation unavailable',
                'message': str(e)
            }

        # STEP 3: Combined Processing Recommendations
        fraud_score = float(fraud_data.get('fraud_score', 0))
        estimated_cost = float(estimate.estimated_cost) if estimate else float(claim.claimed_amount)

        if fraud_score >= 0.8:
            final_recommendation = 'REJECT_CLAIM'
            final_action = 'REJECT'
            priority = 'URGENT'
            reasoning = f"High fraud probability ({fraud_score:.1%}) indicates this claim should be rejected."
        elif fraud_score >= 0.6:
            final_recommendation = 'DETAILED_INVESTIGATION'
            final_action = 'INVESTIGATE'
            priority = 'URGENT'
            reasoning = f"Significant fraud risk ({fraud_score:.1%}) requires detailed investigation before processing."
        elif fraud_score >= 0.4 or estimated_cost > 10000:
            final_recommendation = 'MANUAL_REVIEW'
            final_action = 'REVIEW'
            priority = 'HIGH' if fraud_score >= 0.4 else 'MEDIUM'
            reasoning = f"Moderate risk (fraud: {fraud_score:.1%}, cost: ${estimated_cost:,.0f}) requires manual review."
        elif estimated_cost < 1000:
            final_recommendation = 'AUTO_APPROVE'
            final_action = 'APPROVE'
            priority = 'LOW'
            reasoning = f"Low fraud risk ({fraud_score:.1%}) and low cost (${estimated_cost:,.0f}) qualify for auto-approval."
        else:
            final_recommendation = 'MANUAL_REVIEW'
            final_action = 'REVIEW'
            priority = 'MEDIUM'
            reasoning = "Standard processing recommended for this claim."

        # Build action items
        # DROPPED: if claim.number_of_injuries > 0 — field removed from Claim model
        # DROPPED: if not claim.police_report_filed — field removed from Claim model
        action_items = []

        if fraud_score >= 0.7:
            action_items.append({
                'action': 'Fraud Investigation',
                'priority': 'URGENT',
                'reason': f'High fraud score: {fraud_score:.1%}'
            })

        if estimated_cost > 20000:
            action_items.append({
                'action': 'Senior Adjuster Review',
                'priority': 'HIGH',
                'reason': f'High value claim: ${estimated_cost:,.0f}'
            })

        # Calculate processing time
        processing_time = int((time.time() - start_time) * 1000)

        # Create processing log
        ClaimProcessingLog.objects.create(
            claim=claim,
            estimate=estimate,
            action_type='AUTO_PROCESS',
            action_description=f'Automated claim processing: {final_recommendation}',
            is_automated=True,
            performed_by='SYSTEM',
            result_data={
                'fraud_score': fraud_score,
                'estimated_cost': str(estimated_cost),
                'recommendation': final_recommendation,
                'priority': priority
            },
            processing_time_ms=processing_time,
            model_version='1.0'
        )

        response_data = {
            'claim_id': str(claim.id),
            'claim_number': claim.claim_number,
            'processing_summary': {
                'recommendation': final_recommendation,
                'action': final_action,
                'priority': priority,
                'reasoning': reasoning,
                'confidence': 'HIGH' if fraud_score > 0.7 or fraud_score < 0.3 else 'MEDIUM'
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
                'recommended_reserve': float(estimate.recommended_reserve) if estimate else None
            },
            'action_items': action_items,
            'next_steps': {
                'immediate': final_action,
                'estimated_days': estimate.estimated_processing_days if estimate else None,
                'assigned_priority': priority
            },
            'processing_metadata': {
                'processed_at': timezone.now().isoformat(),
                'processing_time_ms': processing_time,
                'model_version': '1.0',
                'automated': True
            },
            'detailed_fraud_analysis': fraud_data,
            'detailed_estimate': estimate_data
        }

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        import traceback
        print("=" * 70)
        print("ERROR in auto_process_claim:")
        print(traceback.format_exc())
        print("=" * 70)
        return Response(
            {'error': f'Error processing claim: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )