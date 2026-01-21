"""
Train Fraud Detection Model
Combines XGBoost classifier with Isolation Forest for anomaly detection
"""

import os
import sys
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score,
    precision_recall_curve, roc_curve, f1_score
)
from sklearn.ensemble import IsolationForest
import xgboost as xgb
import matplotlib.pyplot as plt
import seaborn as sns

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from apps.fraud_detection.models import Claim, Policyholder, Vehicle, Policy
from ml_models.feature_engineering import FeatureEngineer
from ml_models.ml_config import (
    FRAUD_DETECTION_MODEL_PATH, FRAUD_ISOLATION_FOREST_PATH,
    FRAUD_SCALER_PATH, FRAUD_FEATURES_PATH,
    FRAUD_DETECTION_PARAMS, FRAUD_DETECTION_FEATURES
)


def load_data_from_database():
    """Load data from Django database"""
    print("Loading data from database...")
    
    # Load all data
    claims = Claim.objects.all().values()
    policyholders = Policyholder.objects.all().values()
    vehicles = Vehicle.objects.all().values()
    policies = Policy.objects.all().values()
    
    # Convert to DataFrames
    claims_df = pd.DataFrame(claims)
    policyholders_df = pd.DataFrame(policyholders)
    vehicles_df = pd.DataFrame(vehicles)
    policies_df = pd.DataFrame(policies)
    
    print(f"✓ Loaded {len(claims_df)} claims")
    print(f"✓ Loaded {len(policyholders_df)} policyholders")
    print(f"✓ Loaded {len(vehicles_df)} vehicles")
    print(f"✓ Loaded {len(policies_df)} policies")
    
    return claims_df, policyholders_df, vehicles_df, policies_df


def train_fraud_detection_model():
    """Train fraud detection model"""
    
    print("="*70)
    print("FRAUD DETECTION MODEL TRAINING")
    print("="*70 + "\n")
    
    # Load data
    claims_df, policyholders_df, vehicles_df, policies_df = load_data_from_database()
    
    if len(claims_df) < 50:
        print("ERROR: Not enough claims data. Please generate data first.")
        print("Run: python generate_data.py")
        return
    
    # Feature engineering
    print("\n" + "-"*70)
    print("FEATURE ENGINEERING")
    print("-"*70)
    feature_engineer = FeatureEngineer()
    df = feature_engineer.engineer_fraud_detection_features(
        claims_df, policyholders_df, vehicles_df, policies_df
    )
    
    # Prepare features and target
    X = df[FRAUD_DETECTION_FEATURES].copy()
    y = df['is_fraudulent'].astype(int)
    
    print(f"\nDataset shape: {X.shape}")
    print(f"Fraudulent claims: {y.sum()} ({y.sum()/len(y)*100:.2f}%)")
    print(f"Legitimate claims: {len(y) - y.sum()} ({(len(y)-y.sum())/len(y)*100:.2f}%)")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=FRAUD_DETECTION_PARAMS['test_size'],
        random_state=FRAUD_DETECTION_PARAMS['random_state'],
        stratify=y
    )
    
    print(f"\nTraining set: {len(X_train)} samples")
    print(f"Test set: {len(X_test)} samples")
    
    # Scale features
    print("\nScaling features...")
    X_train_scaled = feature_engineer.scale_features(X_train, fit=True)
    X_test_scaled = feature_engineer.scale_features(X_test, fit=False)
    
    # Train XGBoost model
    print("\n" + "-"*70)
    print("TRAINING XGBOOST CLASSIFIER")
    print("-"*70)
    
    xgb_model = xgb.XGBClassifier(**FRAUD_DETECTION_PARAMS['xgboost'])
    xgb_model.fit(
        X_train_scaled, y_train,
        eval_set=[(X_test_scaled, y_test)],
        verbose=False
    )
    
    # Predictions
    y_pred = xgb_model.predict(X_test_scaled)
    y_pred_proba = xgb_model.predict_proba(X_test_scaled)[:, 1]
    
    # Evaluate XGBoost
    print("\nXGBoost Performance:")
    print(classification_report(y_test, y_pred, target_names=['Legitimate', 'Fraudulent']))
    
    roc_auc = roc_auc_score(y_test, y_pred_proba)
    print(f"ROC-AUC Score: {roc_auc:.4f}")
    
    # Train Isolation Forest for anomaly detection
    print("\n" + "-"*70)
    print("TRAINING ISOLATION FOREST (ANOMALY DETECTION)")
    print("-"*70)
    
    iso_forest = IsolationForest(**FRAUD_DETECTION_PARAMS['isolation_forest'])
    iso_forest.fit(X_train_scaled)
    
    # Anomaly scores (-1 for outliers, 1 for inliers)
    anomaly_scores_test = iso_forest.decision_function(X_test_scaled)
    anomaly_predictions = iso_forest.predict(X_test_scaled)
    anomaly_predictions = (anomaly_predictions == -1).astype(int)  # Convert to 0/1
    
    print(f"\nIsolation Forest detected {anomaly_predictions.sum()} anomalies")
    
    # Combine predictions (ensemble)
    print("\n" + "-"*70)
    print("ENSEMBLE MODEL (XGBoost + Isolation Forest)")
    print("-"*70)
    
    # Combined fraud score: weighted average
    ensemble_score = 0.7 * y_pred_proba + 0.3 * (1 - (anomaly_scores_test + 1) / 2)
    ensemble_pred = (ensemble_score > 0.5).astype(int)
    
    print("\nEnsemble Performance:")
    print(classification_report(y_test, ensemble_pred, target_names=['Legitimate', 'Fraudulent']))
    
    ensemble_roc_auc = roc_auc_score(y_test, ensemble_score)
    print(f"Ensemble ROC-AUC Score: {ensemble_roc_auc:.4f}")
    
    # Feature importance
    print("\n" + "-"*70)
    print("TOP 10 MOST IMPORTANT FEATURES")
    print("-"*70)
    
    feature_importance = pd.DataFrame({
        'feature': FRAUD_DETECTION_FEATURES,
        'importance': xgb_model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print(feature_importance.head(10).to_string(index=False))
    
    # Save models
    print("\n" + "-"*70)
    print("SAVING MODELS")
    print("-"*70)
    
    joblib.dump(xgb_model, FRAUD_DETECTION_MODEL_PATH)
    print(f"✓ Saved XGBoost model to {FRAUD_DETECTION_MODEL_PATH}")
    
    joblib.dump(iso_forest, FRAUD_ISOLATION_FOREST_PATH)
    print(f"✓ Saved Isolation Forest to {FRAUD_ISOLATION_FOREST_PATH}")
    
    feature_engineer.save_scaler(FRAUD_SCALER_PATH)
    joblib.dump(FRAUD_DETECTION_FEATURES, FRAUD_FEATURES_PATH)
    print(f"✓ Saved feature list to {FRAUD_FEATURES_PATH}")
    
    # Save feature importance plot
    plt.figure(figsize=(10, 8))
    top_features = feature_importance.head(15)
    plt.barh(range(len(top_features)), top_features['importance'])
    plt.yticks(range(len(top_features)), top_features['feature'])
    plt.xlabel('Importance')
    plt.title('Top 15 Features for Fraud Detection')
    plt.tight_layout()
    plot_path = FRAUD_DETECTION_MODEL_PATH.parent / 'fraud_feature_importance.png'
    plt.savefig(plot_path)
    print(f"✓ Saved feature importance plot to {plot_path}")
    plt.close()
    
    # Confusion Matrix
    cm = confusion_matrix(y_test, ensemble_pred)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
    plt.title('Fraud Detection Confusion Matrix')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    cm_path = FRAUD_DETECTION_MODEL_PATH.parent / 'fraud_confusion_matrix.png'
    plt.savefig(cm_path)
    print(f"✓ Saved confusion matrix to {cm_path}")
    plt.close()
    
    print("\n" + "="*70)
    print("FRAUD DETECTION MODEL TRAINING COMPLETE")
    print("="*70)
    
    return xgb_model, iso_forest, feature_engineer


if __name__ == '__main__':
    train_fraud_detection_model()