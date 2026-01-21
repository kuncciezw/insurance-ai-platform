"""
Machine Learning Models Configuration
UPDATED VERSION - Improved fraud detection parameters
"""

import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
ML_MODELS_DIR = BASE_DIR / 'ml_models' / 'saved_models'
DATA_DIR = BASE_DIR / 'data' / 'generated'

# Ensure directories exist
ML_MODELS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Model file paths
FRAUD_DETECTION_MODEL_PATH = ML_MODELS_DIR / 'fraud_detection_model.pkl'
FRAUD_ISOLATION_FOREST_PATH = ML_MODELS_DIR / 'isolation_forest_model.pkl'
FRAUD_SCALER_PATH = ML_MODELS_DIR / 'fraud_scaler.pkl'
FRAUD_FEATURES_PATH = ML_MODELS_DIR / 'fraud_features.pkl'
FRAUD_THRESHOLD_PATH = ML_MODELS_DIR / 'fraud_threshold.pkl'  # NEW: Optimal threshold

PRICING_MODEL_PATH = ML_MODELS_DIR / 'pricing_model.pkl'
PRICING_SCALER_PATH = ML_MODELS_DIR / 'pricing_scaler.pkl'
PRICING_FEATURES_PATH = ML_MODELS_DIR / 'pricing_features.pkl'

CLAIMS_ESTIMATOR_PATH = ML_MODELS_DIR / 'claims_estimator_model.pkl'
CLAIMS_SCALER_PATH = ML_MODELS_DIR / 'claims_scaler.pkl'
CLAIMS_FEATURES_PATH = ML_MODELS_DIR / 'claims_features.pkl'

# Training parameters - IMPROVED FOR BETTER FRAUD DETECTION
FRAUD_DETECTION_PARAMS = {
    'test_size': 0.2,
    'random_state': 42,
    'use_smote': True,  # NEW: Enable SMOTE for class balancing
    'augment_fraud_cases': True,  # NEW: Augment minority class
    'augmentation_factor': 5,  # NEW: How many times to augment fraud cases
    'optimal_threshold': 0.4,  # NEW: Lower threshold for better recall
    'xgboost': {
        'n_estimators': 200,
        'max_depth': 5,  # Reduced to prevent overfitting
        'learning_rate': 0.05,  # Lower learning rate for better generalization
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'gamma': 0.1,
        'reg_alpha': 0.1,
        'reg_lambda': 1.0,
        'min_child_weight': 1,  # NEW: Allow more granular splits
        'scale_pos_weight': None,  # Will be calculated dynamically
        'random_state': 42,
        'eval_metric': 'auc'
    },
    'isolation_forest': {
        'contamination': 0.15,  # Increased from 0.1 to detect more anomalies
        'n_estimators': 200,  # Increased for better anomaly detection
        'max_samples': 'auto',  # Let sklearn decide optimal sample size
        'random_state': 42
    }
}

PRICING_MODEL_PARAMS = {
    'test_size': 0.2,
    'random_state': 42,
    'xgboost': {
        'n_estimators': 150,
        'max_depth': 5,
        'learning_rate': 0.1,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'random_state': 42
    }
}

CLAIMS_ESTIMATOR_PARAMS = {
    'test_size': 0.2,
    'random_state': 42,
    'xgboost': {
        'n_estimators': 150,
        'max_depth': 5,
        'learning_rate': 0.1,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'random_state': 42
    }
}

# Feature lists - PRIORITIZED BY IMPORTANCE
FRAUD_DETECTION_FEATURES = [
    # Top importance features (from training)
    'days_since_policy_start',
    'policyholder_claim_count',
    'claim_to_coverage_ratio',
    'submission_delay_hours',
    'number_of_injuries',
    'years_with_company',
    'incident_day_of_week',
    'is_modified',
    'number_of_witnesses',
    'incident_month',
    
    # Secondary features
    'claimed_amount',
    'severity_encoded',
    'claim_type_encoded',
    'vehicle_age',
    'vehicle_value',
    'has_anti_theft',
    'witnesses_present',
    'number_of_vehicles_involved',
    'third_party_involved',
    'policyholder_age',
    'credit_score',
    'incident_hour',
    'police_report_filed'
]

PRICING_FEATURES = [
    # Driver features
    'age',
    'gender_encoded',
    'marital_status_encoded',
    'occupation_encoded',
    'credit_score',
    'years_with_company',
    
    # Vehicle features
    'vehicle_age',
    'vehicle_value',
    'vehicle_type_encoded',
    'fuel_type_encoded',
    'has_anti_theft',
    'has_airbags',
    'has_abs',
    'is_modified',
    'odometer_reading',
    
    # Policy features
    'policy_type_encoded',
    'coverage_level_encoded',
    'coverage_amount',
    'deductible',
    
    # Location features
    'state_encoded'
]

CLAIMS_ESTIMATION_FEATURES = [
    # Claim features
    'claim_type_encoded',
    'severity_encoded',
    
    # Vehicle features
    'vehicle_age',
    'vehicle_value',
    'vehicle_type_encoded',
    
    # Incident features
    'number_of_vehicles_involved',
    'number_of_injuries',
    'third_party_involved',
    'police_report_filed',
    
    # Policy features
    'coverage_amount',
    'deductible',
    'policy_type_encoded'
]

# NEW: Risk level thresholds
FRAUD_RISK_THRESHOLDS = {
    'CRITICAL': 0.8,
    'HIGH': 0.6,
    'MEDIUM': 0.4,
    'LOW': 0.0
}

# NEW: Ensemble weights (Conservative: Trust XGBoost more)
ENSEMBLE_WEIGHTS = {
    'xgboost': 0.8,
    'isolation_forest': 0.2
}