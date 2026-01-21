"""
Feature Engineering Helper for ML Models
FIXED VERSION - Ensures all required fields are present
Place this file in: apps/fraud_detection/ml_feature_engineering.py
"""

from datetime import datetime, date
import pandas as pd
from typing import Dict, Any


def enrich_claim_data(claim, policy=None, vehicle=None, policyholder=None) -> Dict[str, Any]:
    """
    Enrich claim data with related entity information from Django models.
    CRITICAL: This must return ALL fields needed by prepare_claim_features()
    
    Args:
        claim: Claim model instance
        policy: Policy model instance (optional, will use claim.policy if not provided)
        vehicle: Vehicle model instance (optional)
        policyholder: Policyholder model instance (optional)
        
    Returns:
        Enriched claim data dictionary with all info needed for feature engineering
    """
    # Get related objects if not provided
    policy = policy or claim.policy
    vehicle = vehicle or claim.vehicle
    policyholder = policyholder or claim.policyholder
    
    # Calculate policy age at claim time
    if hasattr(claim.submitted_date, 'date'):
        submitted_date = claim.submitted_date.date()
    else:
        submitted_date = claim.submitted_date
    
    policy_age_days = (submitted_date - policy.start_date).days
    
    # Calculate vehicle age
    current_year = date.today().year
    vehicle_age = current_year - vehicle.year
    
    # Get previous claims count for this policyholder
    from apps.fraud_detection.models import Claim
    previous_claims = Claim.objects.filter(
        policyholder=policyholder,
        submitted_date__lt=claim.submitted_date
    ).count()
    
    enriched_data = {
        # Basic claim info (use actual model field names)
        'claim_amount': float(claim.claimed_amount),
        'incident_severity': claim.severity,  # Maps to model's 'severity' field
        'severity': claim.severity,  # Also include as 'severity'
        'incident_type': claim.claim_type,  # Maps to model's 'claim_type' field
        'claim_type': claim.claim_type,  # Also include as 'claim_type'
        'incident_date': claim.incident_date,
        'incident_description': claim.incident_description,
        'filed_date': claim.submitted_date,  # For backward compatibility
        'submitted_date': claim.submitted_date,
        
        # CRITICAL: These were missing and causing the error
        'police_report_filed': bool(claim.police_report_filed),
        'number_of_witnesses': int(claim.number_of_witnesses),
        'number_of_vehicles_involved': int(claim.number_of_vehicles_involved),
        'number_of_injuries': int(claim.number_of_injuries),
        'third_party_involved': bool(claim.third_party_involved),
        
        # Policy info
        'coverage_amount': float(policy.coverage_amount),
        'policy_age_at_claim': policy_age_days,
        
        # CRITICAL: Vehicle info (was missing vehicle_age)
        'vehicle_age': vehicle_age,
        'vehicle_has_alarm': bool(vehicle.has_anti_theft),
        'vehicle_value': float(vehicle.market_value),
        'is_modified': bool(vehicle.is_modified),
        
        # Policyholder info
        'policyholder_age': policyholder.age,
        'credit_score': int(policyholder.credit_score),
        'years_with_company': int(policyholder.years_with_company),
        'previous_claims_count': previous_claims,
    }
    
    return enriched_data


def prepare_claim_features(claim_data: Dict[str, Any]) -> pd.DataFrame:
    """
    Prepare claim data with all required features for ML model.
    This creates features in the EXACT order expected by the trained model.
    
    Args:
        claim_data: Raw claim data dictionary (from enrich_claim_data)
        
    Returns:
        DataFrame with engineered features matching model's expectations
    """
    
    # Extract and calculate all required features
    features = {}
    
    # 1. claimed_amount (raw claim amount)
    features['claimed_amount'] = float(claim_data.get('claim_amount', 0))
    
    # 2. severity_encoded (categorical -> numeric)
    severity_map = {
        'MINOR': 0,
        'MODERATE': 1,
        'MAJOR': 2,
        'TOTAL_LOSS': 3
    }
    severity = claim_data.get('incident_severity', claim_data.get('severity', 'MODERATE'))
    features['severity_encoded'] = severity_map.get(severity, 1)
    
    # 3. claim_type_encoded (categorical -> numeric)
    claim_type_map = {
        'ACCIDENT': 0,
        'THEFT': 1,
        'VANDALISM': 2,
        'NATURAL_DISASTER': 3,
        'FIRE': 4,
        'OTHER': 5
    }
    claim_type = claim_data.get('incident_type', claim_data.get('claim_type', 'OTHER'))
    features['claim_type_encoded'] = claim_type_map.get(claim_type, 5)
    
    # 4. days_since_policy_start
    features['days_since_policy_start'] = int(claim_data.get('policy_age_at_claim', 0))
    
    # 5. claim_to_coverage_ratio
    coverage = max(float(claim_data.get('coverage_amount', 1)), 1)
    features['claim_to_coverage_ratio'] = float(claim_data.get('claim_amount', 0)) / coverage
    
    # 6. vehicle_value
    features['vehicle_value'] = float(claim_data.get('vehicle_value', 20000))
    
    # 7. has_anti_theft (boolean -> 0/1)
    features['has_anti_theft'] = 1 if claim_data.get('vehicle_has_alarm', False) else 0
    
    # 8. is_modified (boolean -> 0/1)
    features['is_modified'] = 1 if claim_data.get('is_modified', False) else 0
    
    # 9. witnesses_present (boolean -> 0/1)
    features['witnesses_present'] = 1 if claim_data.get('number_of_witnesses', 0) > 0 else 0
    
    # 10. number_of_witnesses (raw count)
    features['number_of_witnesses'] = int(claim_data.get('number_of_witnesses', 0))
    
    # 11. number_of_vehicles_involved
    features['number_of_vehicles_involved'] = int(claim_data.get('number_of_vehicles_involved', 1))
    
    # 12. number_of_injuries
    features['number_of_injuries'] = int(claim_data.get('number_of_injuries', 0))
    
    # 13. third_party_involved (boolean -> 0/1)
    features['third_party_involved'] = 1 if claim_data.get('third_party_involved', False) else 0
    
    # 14. policyholder_age
    features['policyholder_age'] = int(claim_data.get('policyholder_age', 35))
    
    # 15. credit_score
    features['credit_score'] = int(claim_data.get('credit_score', 650))
    
    # 16. years_with_company
    features['years_with_company'] = int(claim_data.get('years_with_company', 0))
    
    # 17. policyholder_claim_count
    features['policyholder_claim_count'] = int(claim_data.get('previous_claims_count', 0))
    
    # Extract time-based features from incident date
    incident_date = claim_data.get('incident_date')
    if incident_date:
        if isinstance(incident_date, str):
            try:
                incident_date = datetime.fromisoformat(incident_date.replace('Z', '+00:00'))
            except:
                incident_date = datetime.now()
        
        # 18. incident_hour
        features['incident_hour'] = incident_date.hour if hasattr(incident_date, 'hour') else 12
        
        # 19. incident_day_of_week
        features['incident_day_of_week'] = incident_date.weekday() if hasattr(incident_date, 'weekday') else 0
        
        # 20. incident_month
        features['incident_month'] = incident_date.month if hasattr(incident_date, 'month') else 1
    else:
        features['incident_hour'] = 12
        features['incident_day_of_week'] = 0
        features['incident_month'] = 1
    
    # 21. submission_delay_hours (calculate delay between incident and filing)
    filed_date = claim_data.get('filed_date', claim_data.get('submitted_date'))
    if incident_date and filed_date:
        if isinstance(filed_date, str):
            try:
                filed_date = datetime.fromisoformat(filed_date.replace('Z', '+00:00'))
            except:
                filed_date = datetime.now()
        
        if hasattr(incident_date, 'hour') and hasattr(filed_date, 'hour'):
            try:
                delay = (filed_date - incident_date).total_seconds() / 3600
                features['submission_delay_hours'] = max(0, delay)
            except:
                features['submission_delay_hours'] = 24
        else:
            features['submission_delay_hours'] = 24
    else:
        features['submission_delay_hours'] = 24
    
    # Convert to DataFrame with features in EXACT expected order
    expected_columns = [
        'claimed_amount',
        'severity_encoded',
        'claim_type_encoded',
        'days_since_policy_start',
        'claim_to_coverage_ratio',
        'vehicle_value',
        'has_anti_theft',
        'is_modified',
        'witnesses_present',
        'number_of_witnesses',
        'number_of_vehicles_involved',
        'number_of_injuries',
        'third_party_involved',
        'policyholder_age',
        'credit_score',
        'years_with_company',
        'policyholder_claim_count',
        'incident_hour',
        'incident_day_of_week',
        'incident_month',
        'submission_delay_hours'
    ]
    
    # Create DataFrame with features in correct order
    df = pd.DataFrame([features], columns=expected_columns)
    
    return df


def get_fraud_indicators(claim_data: Dict[str, Any], fraud_score: float) -> list:
    """
    Generate human-readable fraud indicators based on claim data and score.
    
    Args:
        claim_data: Enriched claim data
        fraud_score: Fraud probability score (0-1)
        
    Returns:
        List of fraud indicator strings
    """
    indicators = []
    
    # High claim amount relative to coverage
    claim_to_coverage = claim_data.get('claim_amount', 0) / max(claim_data.get('coverage_amount', 1), 1)
    if claim_to_coverage > 0.9:
        indicators.append("Claim amount near policy coverage limit")
    
    # Recent policy
    if claim_data.get('policy_age_at_claim', 365) < 30:
        indicators.append("Claim filed shortly after policy inception")
    
    # No police report for severe incident
    if claim_data.get('incident_severity') in ['MAJOR', 'TOTAL_LOSS'] and not claim_data.get('police_report_filed'):
        indicators.append("No police report for severe incident")
    
    # No witnesses for severe incident
    if claim_data.get('incident_severity') in ['MAJOR', 'TOTAL_LOSS'] and claim_data.get('number_of_witnesses', 0) == 0:
        indicators.append("No witnesses for severe incident")
    
    # Vague description
    description = claim_data.get('incident_description', '')
    if len(description) < 50:
        indicators.append("Incident description is vague or incomplete")
    
    # Old vehicle with high claim
    vehicle_age = claim_data.get('vehicle_age', 0)
    if vehicle_age > 10 and claim_data.get('claim_amount', 0) > 15000:
        indicators.append("High claim amount for older vehicle")
    
    # Modified vehicle
    if claim_data.get('is_modified'):
        indicators.append("Vehicle has been modified")
    
    # Multiple previous claims
    previous_claims = claim_data.get('previous_claims_count', 0)
    if previous_claims > 2:
        indicators.append(f"Multiple previous claims ({previous_claims})")
    
    # Low credit score
    if claim_data.get('credit_score', 850) < 600:
        indicators.append("Low credit score")
    
    # Theft without anti-theft device
    if claim_data.get('claim_type') == 'THEFT' and not claim_data.get('vehicle_has_alarm'):
        indicators.append("Theft claim without anti-theft device")
    
    # Quick submission (suspiciously fast)
    if claim_data.get('submission_delay_hours', 24) < 2:
        indicators.append("Claim submitted very quickly after incident")
    
    # Late submission (suspicious delay)
    if claim_data.get('submission_delay_hours', 24) > 168:  # 7 days
        indicators.append("Unusual delay in claim submission")
    
    # If no specific indicators but high fraud score
    if not indicators and fraud_score > 0.6:
        indicators.append("Statistical anomaly detected by ML model")
    
    return indicators if indicators else ["No specific fraud indicators detected"]


def get_recommendation(fraud_score: float, risk_level: str) -> str:
    """
    Get recommended action based on fraud score and risk level.
    
    Args:
        fraud_score: Fraud probability (0-1)
        risk_level: Risk classification (LOW, MEDIUM, HIGH, CRITICAL)
        
    Returns:
        Recommendation string
    """
    if risk_level == 'CRITICAL':
        return "URGENT: Immediate investigation required - Assign to senior fraud investigator"
    elif risk_level == 'HIGH':
        return "High priority investigation - Request additional documentation and verification"
    elif risk_level == 'MEDIUM':
        return "Standard verification process - Request supporting evidence"
    else:
        return "Standard processing - Routine claim verification"