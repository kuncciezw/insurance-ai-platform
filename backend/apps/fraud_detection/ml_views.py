"""
ML-Powered Fraud Detection API Views
Provides endpoints for fraud analysis using trained ML models
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta, datetime
import pandas as pd
import numpy as np

from .models import Claim, Policy, Policyholder, Vehicle
from .serializers import ClaimSerializer
from ml_models.model_loader import get_model_loader
from ml_models.feature_engineering import FeatureEngineer


# Initialize model loader (singleton pattern)
model_loader = get_model_loader()
feature_engineer = FeatureEngineer()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_claim_fraud(request):
    """
    Analyze a single claim for fraud
    
    POST /api/fraud-detection/fraud/analyze-claim/
    
    Request Body Option 1 - Existing Claim:
    {
        "claim_id": "uuid-string-here"
    }
    
    Request Body Option 2 - New Claim Data:
    {
        "policy_age_days": 365,
        "claim_delay_days": 5,
        "claimed_amount": 5000,
        "policy_premium": 1200,
        "vehicle_age_years": 5,
        "driver_age": 35,
        "incident_hour": 14,
        "incident_type": "Collision",
        "incident_severity": "Major Damage",
        "authorities_contacted": "Yes",
        "witnesses": 2,
        "previous_claims": 0
    }
    """
    
    try:
        claim_id = request.data.get('claim_id')
        
        if claim_id:
            return _analyze_existing_claim(claim_id)
        else:
            return _analyze_new_claim_data(request.data)
    
    except Exception as e:
        import traceback
        print("="*70)
        print("ERROR in analyze_claim_fraud:")
        print(traceback.format_exc())
        print("="*70)
        return Response(
            {'error': f'Error analyzing claim: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _analyze_existing_claim(claim_id):
    """Analyze an existing claim from the database"""
    try:
        claim = Claim.objects.get(id=claim_id)
    except Claim.DoesNotExist:
        return Response(
            {'error': f'Claim with ID {claim_id} not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        # Get related data
        policy = claim.policy
        policyholder = policy.policyholder
        vehicle = policy.vehicle
        
        print(f"Analyzing claim {claim_id}...")
        print(f"Claim amount: {claim.claimed_amount}")
        print(f"Policy ID: {policy.id}")
        print(f"Policyholder ID: {policyholder.id}")
        
        # Convert to DataFrames - use index numbers for DataFrame operations
        claims_data = {
            'claim_id_str': str(claim.id),  # Keep UUID as string for reference
            'policy_id_str': str(policy.id),
            'policyholder_id_str': str(policyholder.id),
            'vehicle_id_str': str(vehicle.id),
            'claim_type': str(claim.claim_type),
            'severity': str(claim.severity),
            'claimed_amount': float(claim.claimed_amount),
            'incident_date': claim.incident_date,
            'submitted_date': claim.submitted_date,
            'police_report_filed': bool(claim.police_report_filed),
            'witnesses_present': bool(claim.witnesses_present),
            'number_of_witnesses': int(claim.number_of_witnesses or 0),
            'number_of_vehicles_involved': int(claim.number_of_vehicles_involved or 1),
            'number_of_injuries': int(claim.number_of_injuries or 0),
            'third_party_involved': bool(claim.third_party_involved),
        }
        claims_df = pd.DataFrame([claims_data])
        # Add numeric index columns for joins
        claims_df['id'] = 0
        claims_df['policy_id'] = 0
        claims_df['policyholder_id'] = 0
        claims_df['vehicle_id'] = 0
        
        policyholders_data = {
            'policy_holder_id': str(policyholder.policy_holder_id),
            'policyholder_id_str': str(policyholder.id),
            'date_of_birth': policyholder.date_of_birth,
            'credit_score': int(policyholder.credit_score or 650),
            'years_with_company': float(policyholder.years_with_company or 0),
        }
        policyholders_df = pd.DataFrame([policyholders_data])
        policyholders_df['id'] = 0
        
        vehicles_data = {
            'vehicle_id_str': str(vehicle.id),
            'year': int(vehicle.year),
            'market_value': float(vehicle.market_value),
            'has_anti_theft': bool(vehicle.has_anti_theft),
            'is_modified': bool(vehicle.is_modified),
        }
        vehicles_df = pd.DataFrame([vehicles_data])
        vehicles_df['id'] = 0
        
        policies_data = {
            'policy_id_str': str(policy.id),
            'start_date': policy.start_date,
            'coverage_amount': float(policy.coverage_amount),
        }
        policies_df = pd.DataFrame([policies_data])
        policies_df['id'] = 0
        
        print("DataFrames created successfully")
        
        # Engineer features
        engineered_df = feature_engineer.engineer_fraud_detection_features(
            claims_df, policyholders_df, vehicles_df, policies_df
        )
        
        print("Features engineered successfully")
        print(f"Engineered columns: {engineered_df.columns.tolist()}")
        
        # Get fraud prediction
        prediction = model_loader.predict_fraud(engineered_df.iloc[0])
        
        print(f"Prediction: {prediction}")
        
        # Get risk factors
        risk_factors = _get_risk_factors(claim, policy, policyholder)
        
        # Get recommendation
        fraud_prob = float(prediction['fraud_probability'])
        recommendation, automated_action, explanation = _get_recommendation(fraud_prob)
        
        # Build response with explicit type conversion
        response_data = {
            'claim_id': str(claim.id),
            'claim_number': str(claim.claim_number),
            'claimed_amount': float(claim.claimed_amount),
            'fraud_score': round(fraud_prob, 4),
            'is_fraudulent': bool(prediction['is_fraudulent']),
            'fraud_analysis': {
                'fraud_probability': round(fraud_prob, 4),
                'is_fraudulent': bool(prediction['is_fraudulent']),
                'risk_level': str(prediction['risk_level']),
                'confidence': 'high' if fraud_prob > 0.7 or fraud_prob < 0.3 else 'medium',
                'xgboost_probability': round(float(prediction.get('xgboost_probability', fraud_prob)), 4),
                'anomaly_score': round(float(prediction.get('anomaly_score', 0)), 4),
            },
            'risk_factors': risk_factors if risk_factors else ['No significant risk factors detected'],
            'recommendation': str(recommendation),
            'automated_action': str(automated_action),
            'explanation': str(explanation),
            'analyzed_at': timezone.now().isoformat(),
        }
        
        # Update the claim
        claim.fraud_score = fraud_prob
        claim.is_fraudulent = bool(fraud_prob >= 0.6)
        claim.save(update_fields=['fraud_score', 'is_fraudulent'])
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        import traceback
        print("="*70)
        print("ERROR in _analyze_existing_claim:")
        print(traceback.format_exc())
        print("="*70)
        return Response(
            {'error': f'Error analyzing claim: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        

def _analyze_new_claim_data(data):
    """Analyze new claim data provided in the request"""
    
    # Validate required fields
    required_fields = [
        'policy_age_days', 'claim_delay_days', 'claimed_amount', 
        'policy_premium', 'vehicle_age_years', 'driver_age'
    ]
    
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return Response(
            {'error': f'Missing required fields: {", ".join(missing_fields)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Map incident severity
        severity_mapping = {
            'Minor Damage': 'MINOR',
            'Trivial Damage': 'MINOR',
            'Major Damage': 'MAJOR',
            'Total Loss': 'TOTAL_LOSS'
        }
        
        # Map incident type
        type_mapping = {
            'Collision': 'ACCIDENT',
            'Theft': 'THEFT',
            'Fire': 'FIRE',
            'Vandalism': 'VANDALISM',
            'Natural Disaster': 'NATURAL_DISASTER',
            'Other': 'OTHER'
        }
        
        # Create synthetic data
        today = datetime.now()
        incident_date = today - timedelta(days=int(data.get('claim_delay_days', 0)))
        policy_start = today - timedelta(days=int(data.get('policy_age_days', 365)))
        
        # Build DataFrames with numeric IDs for feature engineering
        claims_df = pd.DataFrame([{
            'id': 0,  # Use simple numeric index
            'policy_id': 0,
            'policyholder_id': 0,
            'vehicle_id': 0,
            'claim_type': type_mapping.get(data.get('incident_type', 'Collision'), 'ACCIDENT'),
            'severity': severity_mapping.get(data.get('incident_severity', 'Major Damage'), 'MAJOR'),
            'claimed_amount': float(data['claimed_amount']),
            'incident_date': incident_date,
            'submitted_date': today,
            'police_report_filed': data.get('authorities_contacted', 'No') == 'Yes',
            'witnesses_present': int(data.get('witnesses', 0)) > 0,
            'number_of_witnesses': int(data.get('witnesses', 0)),
            'number_of_vehicles_involved': 2,
            'number_of_injuries': 0,
            'third_party_involved': True,
        }])
        
        birth_year = today.year - int(data.get('driver_age', 35))
        policyholders_df = pd.DataFrame([{
            'policy_holder_id': 'SYNTH000',
            'id': 0,
            'date_of_birth': datetime(birth_year, 1, 1).date(),
            'credit_score': 650,
            'years_with_company': float(data.get('policy_age_days', 365)) / 365,
        }])
        
        current_year = today.year
        vehicle_year = current_year - int(data.get('vehicle_age_years', 5))
        vehicles_df = pd.DataFrame([{
            'id': 0,
            'year': vehicle_year,
            'market_value': float(data.get('claimed_amount', 5000)) * 1.5,
            'has_anti_theft': False,
            'is_modified': False,
        }])
        
        estimated_coverage = float(data['policy_premium']) * 10
        policies_df = pd.DataFrame([{
            'id': 0,
            'start_date': policy_start.date(),
            'coverage_amount': max(estimated_coverage, float(data['claimed_amount']) * 1.2),
        }])
        
        # Engineer features
        engineered_df = feature_engineer.engineer_fraud_detection_features(
            claims_df, policyholders_df, vehicles_df, policies_df
        )
        
        # Get prediction
        prediction = model_loader.predict_fraud(engineered_df.iloc[0])
        
        # Calculate risk factors
        risk_factors = []
        
        if int(data.get('policy_age_days', 365)) < 30:
            risk_factors.append("Very new policy (less than 30 days old)")
        
        if int(data.get('claim_delay_days', 0)) > 7:
            risk_factors.append(f"Delayed claim submission ({data['claim_delay_days']} days)")
        
        claim_to_premium = float(data['claimed_amount']) / float(data['policy_premium'])
        if claim_to_premium > 5:
            risk_factors.append(f"High claim-to-premium ratio ({claim_to_premium:.1f}x)")
        
        if data.get('incident_severity') in ['Major Damage', 'Total Loss']:
            if data.get('authorities_contacted') == 'No':
                risk_factors.append("No police report for severe incident")
        
        if int(data.get('witnesses', 0)) == 0:
            risk_factors.append("No witnesses present")
        
        if int(data.get('previous_claims', 0)) >= 3:
            risk_factors.append(f"Multiple previous claims ({data['previous_claims']})")
        
        incident_hour = int(data.get('incident_hour', 14))
        if incident_hour >= 23 or incident_hour <= 4:
            risk_factors.append(f"Incident occurred during high-risk hours ({incident_hour}:00)")
        
        if int(data.get('vehicle_age_years', 0)) > 10 and float(data['claimed_amount']) > 10000:
            risk_factors.append("High claim amount for older vehicle")
        
        # Build response
        fraud_prob = float(prediction['fraud_probability'])
        recommendation, automated_action, explanation = _get_recommendation(fraud_prob)
        
        response_data = {
            'fraud_score': round(fraud_prob, 4),
            'is_fraudulent': bool(prediction['is_fraudulent']),
            'fraud_analysis': {
                'fraud_probability': round(fraud_prob, 4),
                'is_fraudulent': bool(prediction['is_fraudulent']),
                'risk_level': str(prediction['risk_level']),
                'confidence': 'high' if fraud_prob > 0.7 or fraud_prob < 0.3 else 'medium',
                'xgboost_probability': round(float(prediction.get('xgboost_probability', fraud_prob)), 4),
                'anomaly_score': round(float(prediction.get('anomaly_score', 0)), 4),
            },
            'risk_factors': risk_factors if risk_factors else ['No significant risk factors detected'],
            'recommendation': str(recommendation),
            'automated_action': str(automated_action),
            'explanation': str(explanation),
            'analyzed_at': timezone.now().isoformat(),
            'claim_details': {
                'claimed_amount': float(data['claimed_amount']),
                'incident_type': str(data.get('incident_type')),
                'severity': str(data.get('incident_severity')),
                'policy_age_days': int(data.get('policy_age_days')),
            }
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        import traceback
        print("="*70)
        print("ERROR in _analyze_new_claim_data:")
        print(traceback.format_exc())
        print("="*70)
        return Response(
            {'error': f'Error analyzing claim: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _get_risk_factors(claim, policy, policyholder):
    """Extract risk factors from an existing claim"""
    risk_factors = []
    
    try:
        # Check claim to coverage ratio
        claim_to_coverage = float(claim.claimed_amount) / float(policy.coverage_amount)
        if claim_to_coverage > 0.8:
            risk_factors.append("High claim amount relative to policy coverage")
        
        # Check policy age
        days_since_start = (claim.incident_date.date() - policy.start_date).days
        if days_since_start < 30:
            risk_factors.append("Claim filed shortly after policy inception")
        
        # Check police report
        if claim.severity in ['MAJOR', 'TOTAL_LOSS'] and not claim.police_report_filed:
            risk_factors.append("No police report for severe incident")
        
        # Check submission delay
        submission_delay = (claim.submitted_date - claim.incident_date).total_seconds() / 3600
        if submission_delay > 72:
            risk_factors.append("Delayed claim submission (>72 hours)")
        
        # Check claim history
        policyholder_claims = Claim.objects.filter(
            policy__policyholder=policyholder
        ).count()
        if policyholder_claims >= 3:
            risk_factors.append(f"Multiple claims history ({policyholder_claims} total claims)")
    
    except Exception as e:
        print(f"Error getting risk factors: {e}")
    
    return risk_factors


def _get_recommendation(fraud_prob):
    """Determine recommendation based on fraud probability"""
    if fraud_prob >= 0.8:
        return (
            "REJECT_CLAIM",
            "REJECT",
            "This claim shows strong indicators of fraud and should be rejected."
        )
    elif fraud_prob >= 0.6:
        return (
            "DETAILED_INVESTIGATION",
            "HOLD",
            "This claim requires detailed investigation by fraud specialists."
        )
    elif fraud_prob >= 0.4:
        return (
            "MANUAL_REVIEW",
            "HOLD",
            "This claim should be manually reviewed before processing."
        )
    else:
        return (
            "APPROVE_PROCESSING",
            "PROCEED",
            "This claim shows low fraud risk and can proceed to normal processing."
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def batch_analyze_claims(request):
    """Batch analyze multiple claims for fraud"""
    
    try:
        claim_ids = request.data.get('claim_ids')
        filter_type = request.data.get('filter', 'all_pending')
        
        if claim_ids:
            claims = Claim.objects.filter(id__in=claim_ids)
        elif filter_type == 'all_pending':
            claims = Claim.objects.filter(claim_status__in=['SUBMITTED', 'UNDER_REVIEW'])
        elif filter_type == 'recent':
            date_threshold = timezone.now() - timedelta(days=30)
            claims = Claim.objects.filter(submitted_date__gte=date_threshold)
        elif filter_type == 'high_value':
            claims = Claim.objects.filter(claimed_amount__gte=10000)
        else:
            return Response(
                {'error': 'Invalid filter type'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if claims.count() == 0:
            return Response(
                {'message': 'No claims found', 'results': []},
                status=status.HTTP_200_OK
            )
        
        if claims.count() > 100:
            return Response(
                {'error': f'Batch too large ({claims.count()} claims). Maximum 100.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get related data
        policies = Policy.objects.filter(id__in=claims.values_list('policy_id', flat=True))
        policyholders = Policyholder.objects.filter(
            id__in=policies.values_list('policyholder_id', flat=True)
        )
        vehicles = Vehicle.objects.filter(id__in=policies.values_list('vehicle_id', flat=True))
        
        # Convert to DataFrames with numeric indices
        claims_list = list(claims.values())
        for i, claim in enumerate(claims_list):
            claim['numeric_id'] = i
        claims_df = pd.DataFrame(claims_list)
        claims_df['id'] = claims_df['numeric_id']
        
        policyholders_df = pd.DataFrame(list(policyholders.values()))
        vehicles_df = pd.DataFrame(list(vehicles.values()))
        policies_df = pd.DataFrame(list(policies.values()))
        
        # Create ID mappings
        policy_id_map = {str(p['id']): i for i, p in enumerate(policies_df.to_dict('records'))}
        policyholder_id_map = {str(p['id']): i for i, p in enumerate(policyholders_df.to_dict('records'))}
        vehicle_id_map = {str(v['id']): i for i, v in enumerate(vehicles_df.to_dict('records'))}
        
        # Map UUIDs to numeric IDs
        claims_df['policy_id'] = claims_df['policy_id'].astype(str).map(policy_id_map).fillna(0).astype(int)
        policies_df['id'] = range(len(policies_df))
        policies_df['policyholder_id'] = policies_df['policyholder_id'].astype(str).map(policyholder_id_map).fillna(0).astype(int)
        policies_df['vehicle_id'] = policies_df['vehicle_id'].astype(str).map(vehicle_id_map).fillna(0).astype(int)
        policyholders_df['id'] = range(len(policyholders_df))
        vehicles_df['id'] = range(len(vehicles_df))
        
        # Engineer features
        engineered_df = feature_engineer.engineer_fraud_detection_features(
            claims_df, policyholders_df, vehicles_df, policies_df
        )
        
        # Get predictions
        results = []
        risk_counts = {'HIGH': 0, 'CRITICAL': 0, 'MEDIUM': 0, 'LOW': 0}
        
        for idx, row in engineered_df.iterrows():
            prediction = model_loader.predict_fraud(row)
            original_claim = claims_list[idx]
            
            risk_level = str(prediction['risk_level'])
            risk_counts[risk_level] += 1
            
            results.append({
                'claim_id': str(original_claim['id']),
                'claim_number': str(original_claim['claim_number']),
                'claimed_amount': float(original_claim['claimed_amount']),
                'fraud_probability': round(float(prediction['fraud_probability']), 4),
                'risk_level': risk_level,
                'is_fraudulent': bool(prediction['is_fraudulent']),
            })
        
        results.sort(key=lambda x: x['fraud_probability'], reverse=True)
        
        return Response({
            'total_analyzed': len(results),
            'high_risk_count': risk_counts['HIGH'] + risk_counts['CRITICAL'],
            'medium_risk_count': risk_counts['MEDIUM'],
            'low_risk_count': risk_counts['LOW'],
            'risk_breakdown': risk_counts,
            'results': results,
            'analyzed_at': timezone.now().isoformat(),
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return Response(
            {'error': f'Error in batch analysis: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_high_risk_claims(request):
    """Get list of high-risk claims"""
    
    try:
        threshold = float(request.GET.get('threshold', 0.6))
        limit = min(int(request.GET.get('limit', 20)), 100)
        
        claims = Claim.objects.filter(
            fraud_score__gte=threshold
        ).select_related('policy', 'policy__policyholder', 'policy__vehicle')[:limit]
        
        results = []
        for claim in claims:
            results.append({
                'claim_id': str(claim.id),
                'claim_number': str(claim.claim_number),
                'claimed_amount': float(claim.claimed_amount),
                'claim_type': str(claim.claim_type),
                'severity': str(claim.severity),
                'fraud_probability': round(float(claim.fraud_score or 0), 4),
                'submitted_date': claim.submitted_date.isoformat(),
                'policyholder_name': f"{claim.policy.policyholder.first_name} {claim.policy.policyholder.last_name}",
            })
        
        return Response({
            'count': len(results),
            'threshold': threshold,
            'results': results,
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': f'Error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fraud_statistics(request):
    """Get fraud detection statistics"""
    
    try:
        total_claims = Claim.objects.count()
        fraudulent_claims = Claim.objects.filter(is_fraudulent=True).count()
        high_fraud_score = Claim.objects.filter(fraud_score__gte=0.7).count()
        
        fraud_rate = fraudulent_claims / total_claims if total_claims > 0 else 0
        avg_fraud_score = Claim.objects.aggregate(Avg('fraud_score'))['fraud_score__avg'] or 0
        
        # By claim type
        by_claim_type = {}
        for claim_type in ['ACCIDENT', 'THEFT', 'VANDALISM', 'NATURAL_DISASTER', 'FIRE', 'OTHER']:
            count = Claim.objects.filter(claim_type=claim_type, is_fraudulent=True).count()
            total = Claim.objects.filter(claim_type=claim_type).count()
            by_claim_type[claim_type] = {
                'fraudulent': count,
                'total': total,
                'fraud_rate': count / total if total > 0 else 0
            }
        
        # By severity
        by_severity = {}
        for severity in ['MINOR', 'MODERATE', 'MAJOR', 'TOTAL_LOSS']:
            count = Claim.objects.filter(severity=severity, is_fraudulent=True).count()
            total = Claim.objects.filter(severity=severity).count()
            by_severity[severity] = {
                'fraudulent': count,
                'total': total,
                'fraud_rate': count / total if total > 0 else 0
            }
        
        return Response({
            'total_claims': total_claims,
            'fraudulent_claims': fraudulent_claims,
            'high_risk_claims': high_fraud_score,
            'fraud_rate': round(fraud_rate, 4),
            'average_fraud_score': round(avg_fraud_score, 4),
            'by_claim_type': by_claim_type,
            'by_severity': by_severity,
            'generated_at': timezone.now().isoformat(),
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': f'Error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )