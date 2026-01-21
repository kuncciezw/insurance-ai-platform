"""
Model Loading and Prediction Utilities
FIXED VERSION - Added prediction capping to prevent database overflow
"""

import os
import sys
import joblib
import numpy as np
import pandas as pd
from pathlib import Path

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from ml_models.ml_config import (
    FRAUD_DETECTION_MODEL_PATH,
    FRAUD_ISOLATION_FOREST_PATH,
    FRAUD_SCALER_PATH,
    FRAUD_FEATURES_PATH,
    FRAUD_THRESHOLD_PATH,
    PRICING_MODEL_PATH,
    PRICING_SCALER_PATH,
    PRICING_FEATURES_PATH,
    CLAIMS_ESTIMATOR_PATH,
    CLAIMS_SCALER_PATH,
    CLAIMS_FEATURES_PATH,
    FRAUD_RISK_THRESHOLDS,
    ENSEMBLE_WEIGHTS
)
from ml_models.feature_engineering import FeatureEngineer

# ============================================================================
# CRITICAL FIX: Database field limits
# ============================================================================
MAX_CLAIM_AMOUNT = 9999999999.99  # Database limit: 12 digits total, 2 decimal
MAX_SAFE_AMOUNT = 9999999999.00   # Leave margin for safety


class ModelLoader:
    """Handles loading and using trained ML models"""
    
    def __init__(self):
        self.fraud_model = None
        self.fraud_isolation_forest = None
        self.fraud_scaler = None
        self.fraud_features = None
        self.fraud_threshold = 0.4
        
        self.pricing_model = None
        self.pricing_scaler = None
        self.pricing_features = None
        
        self.claims_estimator = None
        self.claims_scaler = None
        self.claims_features = None
        
        self.feature_engineer = FeatureEngineer()
        
    def load_fraud_detection_model(self):
        """Load fraud detection models"""
        try:
            if not FRAUD_DETECTION_MODEL_PATH.exists():
                raise FileNotFoundError(f"Fraud detection model not found at {FRAUD_DETECTION_MODEL_PATH}")
            
            self.fraud_model = joblib.load(FRAUD_DETECTION_MODEL_PATH)
            self.fraud_isolation_forest = joblib.load(FRAUD_ISOLATION_FOREST_PATH)
            self.fraud_scaler = joblib.load(FRAUD_SCALER_PATH)
            self.fraud_features = joblib.load(FRAUD_FEATURES_PATH)
            
            if FRAUD_THRESHOLD_PATH.exists():
                threshold_data = joblib.load(FRAUD_THRESHOLD_PATH)
                self.fraud_threshold = threshold_data.get('optimal_threshold', 0.4)
                print(f"✓ Loaded optimal fraud threshold: {self.fraud_threshold}")
            else:
                print(f"⚠️ Using default threshold: {self.fraud_threshold}")
            
            print("✓ Loaded fraud detection models")
            return True
        except Exception as e:
            print(f"✗ Error loading fraud detection model: {e}")
            return False
    
    def load_pricing_model(self):
        """Load dynamic pricing model"""
        try:
            if not PRICING_MODEL_PATH.exists():
                raise FileNotFoundError(f"Pricing model not found at {PRICING_MODEL_PATH}")
            
            self.pricing_model = joblib.load(PRICING_MODEL_PATH)
            self.pricing_scaler = joblib.load(PRICING_SCALER_PATH)
            self.pricing_features = joblib.load(PRICING_FEATURES_PATH)
            
            print("✓ Loaded pricing model")
            return True
        except Exception as e:
            print(f"✗ Error loading pricing model: {e}")
            return False
    
    def load_claims_estimator(self):
        """Load claims cost estimation model"""
        try:
            if not CLAIMS_ESTIMATOR_PATH.exists():
                raise FileNotFoundError(f"Claims estimator not found at {CLAIMS_ESTIMATOR_PATH}")
            
            self.claims_estimator = joblib.load(CLAIMS_ESTIMATOR_PATH)
            self.claims_scaler = joblib.load(CLAIMS_SCALER_PATH)
            self.claims_features = joblib.load(CLAIMS_FEATURES_PATH)
            
            print("✓ Loaded claims estimator model")
            return True
        except Exception as e:
            print(f"✗ Error loading claims estimator: {e}")
            return False
    
    def load_all_models(self):
        """Load all trained models"""
        print("Loading all ML models...")
        print("-" * 50)
        
        fraud_loaded = self.load_fraud_detection_model()
        pricing_loaded = self.load_pricing_model()
        claims_loaded = self.load_claims_estimator()
        
        print("-" * 50)
        if fraud_loaded and pricing_loaded and claims_loaded:
            print("✅ All models loaded successfully!")
            return True
        else:
            print("⚠️ Some models failed to load. Check errors above.")
            return False
    
    def predict_fraud(self, claim_data):
        """
        Predict fraud probability for a claim - ENHANCED VERSION
        
        Args:
            claim_data: Dictionary, Series, or DataFrame with claim features
            
        Returns:
            dict: {
                'fraud_probability': float,
                'is_fraudulent': bool,
                'risk_level': str,
                'anomaly_score': float,
                'xgboost_probability': float,
                'threshold_used': float,
                'confidence': str
            }
        """
        if self.fraud_model is None:
            self.load_fraud_detection_model()
        
        # Convert to DataFrame if dictionary or Series
        if isinstance(claim_data, dict):
            df = pd.DataFrame([claim_data])
        elif isinstance(claim_data, pd.Series):
            df = pd.DataFrame([claim_data])
        else:
            df = claim_data.copy()
        
        # Ensure all required features are present
        missing_features = [f for f in self.fraud_features if f not in df.columns]
        if missing_features:
            print(f"⚠️ Missing features, adding with default values: {missing_features[:5]}")
            for feat in missing_features:
                df[feat] = 0
        
        # Extract features in correct order
        X = df[self.fraud_features].copy()
        
        # Fill NaN values
        X = X.fillna(0).infer_objects(copy=False)
        
        # Scale features
        X_scaled = self.fraud_scaler.transform(X)
        
        # Get XGBoost predictions
        fraud_proba = self.fraud_model.predict_proba(X_scaled)[:, 1]
        
        # Get anomaly scores from Isolation Forest
        anomaly_scores_raw = -self.fraud_isolation_forest.score_samples(X_scaled)
        
        # Normalize anomaly scores to 0-1 range
        anomaly_min = -0.5
        anomaly_max = 0.5
        anomaly_scores = np.clip(
            (anomaly_scores_raw - anomaly_min) / (anomaly_max - anomaly_min),
            0, 1
        )
        
        # Ensemble prediction using configured weights
        xgb_weight = ENSEMBLE_WEIGHTS['xgboost']
        iso_weight = ENSEMBLE_WEIGHTS['isolation_forest']
        combined_score = (fraud_proba * xgb_weight + anomaly_scores * iso_weight)
        
        # Use optimal threshold for classification
        is_fraudulent = combined_score[0] >= self.fraud_threshold
        
        # Determine risk level using configured thresholds
        if combined_score[0] >= FRAUD_RISK_THRESHOLDS['CRITICAL']:
            risk_level = 'CRITICAL'
        elif combined_score[0] >= FRAUD_RISK_THRESHOLDS['HIGH']:
            risk_level = 'HIGH'
        elif combined_score[0] >= FRAUD_RISK_THRESHOLDS['MEDIUM']:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'
        
        # Determine confidence level
        if combined_score[0] > 0.7 or combined_score[0] < 0.3:
            confidence = 'high'
        else:
            confidence = 'medium'
        
        return {
            'fraud_probability': float(combined_score[0]),
            'is_fraudulent': bool(is_fraudulent),
            'risk_level': risk_level,
            'anomaly_score': float(anomaly_scores[0]),
            'xgboost_probability': float(fraud_proba[0]),
            'threshold_used': float(self.fraud_threshold),
            'confidence': confidence,
            'ensemble_weights': {
                'xgboost': xgb_weight,
                'isolation_forest': iso_weight
            }
        }
    
    def predict_premium(self, policy_data):
        """
        Predict insurance premium
        
        Args:
            policy_data: Dictionary, Series, or DataFrame with policy features
            
        Returns:
            dict: {
                'predicted_premium': float,
                'confidence_interval': tuple
            }
        """
        if self.pricing_model is None:
            self.load_pricing_model()
        
        # Convert to DataFrame if dictionary or Series
        if isinstance(policy_data, dict):
            df = pd.DataFrame([policy_data])
        elif isinstance(policy_data, pd.Series):
            df = pd.DataFrame([policy_data])
        else:
            df = policy_data.copy()
        
        # Extract features
        X = df[self.pricing_features].copy()
        
        # Fill NaN values
        X = X.fillna(0).infer_objects(copy=False)
        
        # Scale features
        X_scaled = self.pricing_scaler.transform(X)
        
        # Get prediction
        premium_pred = self.pricing_model.predict(X_scaled)
        
        # Ensure non-negative
        premium_pred = np.maximum(premium_pred, 0)
        
        # Calculate confidence interval (approximate)
        lower_bound = premium_pred * 0.85
        upper_bound = premium_pred * 1.15
        
        return {
            'predicted_premium': float(premium_pred[0]),
            'confidence_interval': (float(lower_bound[0]), float(upper_bound[0])),
            'monthly_premium': float(premium_pred[0] / 12)
        }
    
    def estimate_claim_cost(self, claim_data):
        """
        Estimate claim settlement cost - FIXED VERSION WITH CAPPING
        
        Args:
            claim_data: Dictionary, Series, or DataFrame with claim features
            
        Returns:
            dict: {
                'estimated_cost': float,
                'confidence_interval': tuple,
                'severity': str,
                'recommended_reserve': float,
                'capped': bool  # NEW: indicates if amount was capped
            }
        """
        if self.claims_estimator is None:
            self.load_claims_estimator()
        
        # Convert to DataFrame if dictionary or Series
        if isinstance(claim_data, dict):
            df = pd.DataFrame([claim_data])
        elif isinstance(claim_data, pd.Series):
            df = pd.DataFrame([claim_data])
        else:
            df = claim_data.copy()
        
        # Extract features
        X = df[self.claims_features].copy()
        
        # Fill NaN values
        X = X.fillna(0).infer_objects(copy=False)
        
        # Scale features
        X_scaled = self.claims_scaler.transform(X)
        
        # Get prediction
        cost_pred = self.claims_estimator.predict(X_scaled)
        
        # Ensure non-negative
        cost_pred = np.maximum(cost_pred, 0)
        
        # ============================================================
        # CRITICAL FIX: Cap prediction at database maximum
        # ============================================================
        was_capped = False
        if cost_pred[0] > MAX_SAFE_AMOUNT:
            print(f"⚠️ CAPPING: ML predicted ${cost_pred[0]:,.2f}, capping to ${MAX_SAFE_AMOUNT:,.2f}")
            cost_pred[0] = MAX_SAFE_AMOUNT
            was_capped = True
        
        # Calculate confidence interval
        # Cap these as well
        lower_bound = min(cost_pred[0] * 0.80, MAX_SAFE_AMOUNT)
        upper_bound = min(cost_pred[0] * 1.20, MAX_SAFE_AMOUNT)
        
        # Ensure upper bound isn't less than prediction
        if upper_bound < cost_pred[0]:
            upper_bound = cost_pred[0]
        
        # Recommended reserve should also be capped
        recommended_reserve = min(upper_bound, MAX_SAFE_AMOUNT)
        
        # Determine severity
        severity_encoded = X['severity_encoded'].values[0]
        severity_map = {0: 'Minor', 1: 'Moderate', 2: 'Major', 3: 'Critical'}
        severity = severity_map.get(int(severity_encoded), 'Unknown')
        
        return {
            'estimated_cost': float(cost_pred[0]),
            'confidence_interval': (float(lower_bound), float(upper_bound)),
            'severity': severity,
            'recommended_reserve': float(recommended_reserve),
            'capped': was_capped,  # NEW: transparency flag
            'max_allowed': float(MAX_SAFE_AMOUNT)  # NEW: for reference
        }
    
    def batch_predict_fraud(self, claims_df):
        """Predict fraud for multiple claims"""
        if self.fraud_model is None:
            self.load_fraud_detection_model()
        
        results = []
        for idx, row in claims_df.iterrows():
            prediction = self.predict_fraud(row.to_dict())
            prediction['claim_id'] = idx
            results.append(prediction)
        
        return pd.DataFrame(results)
    
    def batch_predict_premium(self, policies_df):
        """Predict premiums for multiple policies"""
        if self.pricing_model is None:
            self.load_pricing_model()
        
        results = []
        for idx, row in policies_df.iterrows():
            prediction = self.predict_premium(row.to_dict())
            prediction['policy_id'] = idx
            results.append(prediction)
        
        return pd.DataFrame(results)
    
    def batch_estimate_claims(self, claims_df):
        """Estimate costs for multiple claims"""
        if self.claims_estimator is None:
            self.load_claims_estimator()
        
        results = []
        for idx, row in claims_df.iterrows():
            estimation = self.estimate_claim_cost(row.to_dict())
            estimation['claim_id'] = idx
            results.append(estimation)
        
        return pd.DataFrame(results)


# Singleton instance for easy access
_model_loader_instance = None

def get_model_loader():
    """Get or create ModelLoader singleton instance"""
    global _model_loader_instance
    if _model_loader_instance is None:
        _model_loader_instance = ModelLoader()
        _model_loader_instance.load_all_models()
    return _model_loader_instance


# Test functions remain the same...
def test_fraud_detection():
    """Test fraud detection model"""
    print("\n" + "="*70)
    print("TESTING FRAUD DETECTION MODEL")
    print("="*70)
    
    from apps.fraud_detection.models import Claim, Policyholder, Vehicle, Policy
    from ml_models.feature_engineering import FeatureEngineer
    
    claims = Claim.objects.all()[:10].values()
    if not claims:
        print("No claims found in database!")
        return
    
    policyholders = Policyholder.objects.all().values()
    vehicles = Vehicle.objects.all().values()
    policies = Policy.objects.all().values()
    
    claims_df = pd.DataFrame(claims)
    policyholders_df = pd.DataFrame(policyholders)
    vehicles_df = pd.DataFrame(vehicles)
    policies_df = pd.DataFrame(policies)
    
    feature_engineer = FeatureEngineer()
    df = feature_engineer.engineer_fraud_detection_features(
        claims_df, policyholders_df, vehicles_df, policies_df
    )
    
    loader = get_model_loader()
    
    print("\nSample Predictions:")
    print("-" * 70)
    for i in range(min(5, len(df))):
        result = loader.predict_fraud(df.iloc[i])
        print(f"\nClaim {i+1}:")
        print(f"  Fraud Probability: {result['fraud_probability']:.2%}")
        print(f"  XGBoost Probability: {result['xgboost_probability']:.2%}")
        print(f"  Anomaly Score: {result['anomaly_score']:.2%}")
        print(f"  Risk Level: {result['risk_level']}")
        print(f"  Classification: {'FRAUDULENT' if result['is_fraudulent'] else 'LEGITIMATE'}")
        print(f"  Threshold: {result['threshold_used']:.2f}")
        print(f"  Confidence: {result['confidence']}")


def test_pricing_model():
    """Test pricing model"""
    print("\n" + "="*70)
    print("TESTING PRICING MODEL")
    print("="*70)
    
    from apps.fraud_detection.models import Policyholder, Vehicle, Policy
    from ml_models.feature_engineering import FeatureEngineer
    
    policyholders = Policyholder.objects.all()[:10].values()
    vehicles = Vehicle.objects.all()[:10].values()
    policies = Policy.objects.all()[:10].values()
    
    if not policies:
        print("No policies found in database!")
        return
    
    policyholders_df = pd.DataFrame(policyholders)
    vehicles_df = pd.DataFrame(vehicles)
    policies_df = pd.DataFrame(policies)
    
    feature_engineer = FeatureEngineer()
    df = feature_engineer.engineer_pricing_features(
        policyholders_df, vehicles_df, policies_df
    )
    
    loader = get_model_loader()
    
    print("\nSample Predictions:")
    print("-" * 70)
    for i in range(min(5, len(df))):
        result = loader.predict_premium(df.iloc[i])
        print(f"\nPolicy {i+1}:")
        print(f"  Predicted Annual Premium: ${result['predicted_premium']:.2f}")
        print(f"  Monthly Premium: ${result['monthly_premium']:.2f}")
        print(f"  Confidence Interval: ${result['confidence_interval'][0]:.2f} - ${result['confidence_interval'][1]:.2f}")


def test_claims_estimator():
    """Test claims cost estimator"""
    print("\n" + "="*70)
    print("TESTING CLAIMS COST ESTIMATOR")
    print("="*70)
    
    from apps.fraud_detection.models import Claim, Vehicle, Policy
    from ml_models.feature_engineering import FeatureEngineer
    
    claims = Claim.objects.all()[:10].values()
    vehicles = Vehicle.objects.all().values()
    policies = Policy.objects.all().values()
    
    if not claims:
        print("No claims found in database!")
        return
    
    claims_df = pd.DataFrame(claims)
    vehicles_df = pd.DataFrame(vehicles)
    policies_df = pd.DataFrame(policies)
    
    feature_engineer = FeatureEngineer()
    df = feature_engineer.engineer_claims_estimation_features(
        claims_df, vehicles_df, policies_df
    )
    
    loader = get_model_loader()
    
    print("\nSample Predictions:")
    print("-" * 70)
    for i in range(min(5, len(df))):
        result = loader.estimate_claim_cost(df.iloc[i])
        print(f"\nClaim {i+1}:")
        print(f"  Estimated Cost: ${result['estimated_cost']:,.2f}")
        print(f"  Severity: {result['severity']}")
        print(f"  Confidence Interval: ${result['confidence_interval'][0]:,.2f} - ${result['confidence_interval'][1]:,.2f}")
        print(f"  Recommended Reserve: ${result['recommended_reserve']:,.2f}")
        if result.get('capped'):
            print(f"  ⚠️ CAPPED at maximum allowed: ${result['max_allowed']:,.2f}")


if __name__ == '__main__':
    # Test all models
    test_fraud_detection()
    test_pricing_model()
    test_claims_estimator()
    
    print("\n" + "="*70)
    print("✅ ALL MODEL TESTS COMPLETE")
    print("="*70)