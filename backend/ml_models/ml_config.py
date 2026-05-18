"""
Machine Learning Models Configuration
"""

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Base directories
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
ML_MODELS_DIR = BASE_DIR / 'ml_models' / 'saved_models'
DATA_DIR = BASE_DIR / 'data' / 'generated'

# Ensure directories exist
ML_MODELS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Model file paths
# ---------------------------------------------------------------------------
FRAUD_DETECTION_MODEL_PATH  = ML_MODELS_DIR / 'fraud_detection_model.pkl'
FRAUD_ISOLATION_FOREST_PATH = ML_MODELS_DIR / 'isolation_forest_model.pkl'
FRAUD_SCALER_PATH           = ML_MODELS_DIR / 'fraud_scaler.pkl'
FRAUD_FEATURES_PATH         = ML_MODELS_DIR / 'fraud_features.pkl'
FRAUD_THRESHOLD_PATH        = ML_MODELS_DIR / 'fraud_threshold.pkl'

PRICING_MODEL_PATH    = ML_MODELS_DIR / 'pricing_model.pkl'
PRICING_SCALER_PATH   = ML_MODELS_DIR / 'pricing_scaler.pkl'
PRICING_FEATURES_PATH = ML_MODELS_DIR / 'pricing_features.pkl'

CLAIMS_ESTIMATOR_PATH  = ML_MODELS_DIR / 'claims_estimator_model.pkl'
CLAIMS_SCALER_PATH     = ML_MODELS_DIR / 'claims_scaler.pkl'
CLAIMS_FEATURES_PATH   = ML_MODELS_DIR / 'claims_features.pkl'

# ---------------------------------------------------------------------------
# Training parameters
# ---------------------------------------------------------------------------
FRAUD_DETECTION_PARAMS = {
    'test_size': 0.2,
    'random_state': 42,

    # SMOTE flags — used dynamically by train_fraud_detection.py
    'use_smote': True,
    'sampling_strategy': 0.5,   # Balance minority to 50 % of majority
    'smote_k_neighbors': 3,     # Conservative; overridden at runtime if needed

    'optimal_threshold': 0.5,   # Starting threshold; best is chosen via grid search

    'xgboost': {
        'n_estimators': 100,        # Reduced to prevent overfitting
        'max_depth': 4,             # Conservative depth
        'learning_rate': 0.1,
        'subsample': 0.7,
        'colsample_bytree': 0.7,
        'gamma': 0.2,               # Regularisation — minimum loss reduction
        'reg_alpha': 0.3,           # L1 regularisation
        'reg_lambda': 2.0,          # L2 regularisation
        'min_child_weight': 3,      # Prevents over-splitting on sparse fraud cases
        'scale_pos_weight': None,   # Calculated dynamically from class counts
        'objective': 'binary:logistic',
        'random_state': 42,
        'eval_metric': 'auc',
    },

    'isolation_forest': {
        'n_estimators': 100,
        'contamination': 0.1,       # Conservative — trained only on legit claims
        'max_samples': 'auto',
        'random_state': 42,
    },
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
        'random_state': 42,
    },
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
        'random_state': 42,
    },
}

# ---------------------------------------------------------------------------
# Feature lists
# ---------------------------------------------------------------------------
FRAUD_DETECTION_FEATURES = [
    # High-importance temporal / policy signals
    'days_since_policy_start',
    'policyholder_claim_count',
    'claim_to_coverage_ratio',
    'submission_delay_hours',
    'years_with_company',
    'incident_day_of_week',
    'incident_month',
    'incident_hour',

    # Claim descriptors
    'claimed_amount',
    'severity_encoded',
    'claim_type_encoded',

    # Vehicle signals
    'vehicle_age',
    'vehicle_value',
    'has_anti_theft',
    'is_modified',

    # Incident scope
    'number_of_vehicles_involved',

    # Policyholder risk profile
    'policyholder_age',
    'credit_score',
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

    # Location
    'state_encoded',
]

CLAIMS_ESTIMATION_FEATURES = [
    # Claim descriptors
    'claim_type_encoded',
    'severity_encoded',

    # Vehicle signals
    'vehicle_age',
    'vehicle_value',
    'vehicle_type_encoded',

    # Incident scope
    'number_of_vehicles_involved',

    # Policy financials
    'coverage_amount',
    'deductible',
    'policy_type_encoded',
]

# ---------------------------------------------------------------------------
# Risk-level thresholds for fraud ensemble score (0-1)
# ---------------------------------------------------------------------------
FRAUD_RISK_THRESHOLDS = {
    'CRITICAL': 0.8,
    'HIGH':     0.6,
    'MEDIUM':   0.4,
    'LOW':      0.0,
}

# ---------------------------------------------------------------------------
# Ensemble weights — XGBoost trusted more than Isolation Forest
# ---------------------------------------------------------------------------
ENSEMBLE_WEIGHTS = {
    'xgboost':          0.8,
    'isolation_forest': 0.2,
}