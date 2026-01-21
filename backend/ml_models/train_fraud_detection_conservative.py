"""
Conservative Fraud Detection Model Training
More conservative approach that avoids overfitting
Save as: ml_models/train_fraud_detection_conservative.py
"""

import os
import sys
import django
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Django setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, roc_curve
from sklearn.ensemble import IsolationForest
from imblearn.over_sampling import SMOTE
import xgboost as xgb
import joblib

from apps.fraud_detection.models import Claim, Policy, Policyholder, Vehicle
from ml_models.feature_engineering import FeatureEngineer


def load_data():
    """Load data from database"""
    print("\nLoading data from database...")
    
    claims = list(Claim.objects.all().values())
    policyholders = list(Policyholder.objects.all().values())
    vehicles = list(Vehicle.objects.all().values())
    policies = list(Policy.objects.all().values())
    
    claims_df = pd.DataFrame(claims)
    policyholders_df = pd.DataFrame(policyholders)
    vehicles_df = pd.DataFrame(vehicles)
    policies_df = pd.DataFrame(policies)
    
    print(f"✓ Loaded {len(claims_df)} claims")
    print(f"✓ Loaded {len(policyholders_df)} policyholders")
    print(f"✓ Loaded {len(vehicles_df)} vehicles")
    print(f"✓ Loaded {len(policies_df)} policies")
    
    return claims_df, policyholders_df, vehicles_df, policies_df


def train_conservative_model():
    """Train fraud detection model with conservative approach"""
    
    print("=" * 70)
    print("CONSERVATIVE FRAUD DETECTION MODEL TRAINING")
    print("=" * 70)
    
    # Load data
    claims_df, policyholders_df, vehicles_df, policies_df = load_data()
    
    # Feature engineering
    print("\n" + "-" * 70)
    print("FEATURE ENGINEERING")
    print("-" * 70)
    
    feature_engineer = FeatureEngineer()
    df = feature_engineer.engineer_fraud_detection_features(
        claims_df, policyholders_df, vehicles_df, policies_df
    )
    
    # Define target and features
    target_col = 'is_fraudulent'
    
    # Use only the most important features
    important_features = [
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
    
    available_features = [f for f in important_features if f in df.columns]
    
    X = df[available_features].copy()
    y = df[target_col].copy()
    
    # Fill NaN values
    X = X.fillna(0)
    
    print(f"\nOriginal Dataset:")
    print(f"Total samples: {len(X)}")
    print(f"Fraudulent claims: {y.sum()} ({y.sum()/len(y)*100:.2f}%)")
    print(f"Legitimate claims: {(~y).sum()} ({(~y).sum()/len(y)*100:.2f}%)")
    
    # Split FIRST, then apply SMOTE only to training data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"\nBefore SMOTE:")
    print(f"Training samples: {len(X_train)}")
    print(f"Training fraud rate: {y_train.sum()/len(y_train)*100:.2f}%")
    print(f"Test samples: {len(X_test)}")
    print(f"Test fraud rate: {y_test.sum()/len(y_test)*100:.2f}%")
    
    # Scale features
    print("\nScaling features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Apply SMOTE only to training data with k_neighbors=min(5, fraud_count-1)
    fraud_count = y_train.sum()
    k_neighbors = min(3, max(1, fraud_count - 1))  # Conservative k_neighbors
    
    print(f"\nApplying SMOTE with k_neighbors={k_neighbors}...")
    smote = SMOTE(random_state=42, k_neighbors=k_neighbors, sampling_strategy=0.5)  # Only 50% balance
    X_train_balanced, y_train_balanced = smote.fit_resample(X_train_scaled, y_train)
    
    print(f"After SMOTE:")
    print(f"Training samples: {len(X_train_balanced)}")
    print(f"Training fraud rate: {y_train_balanced.sum()/len(y_train_balanced)*100:.2f}%")
    
    # Calculate class weight
    fraud_count_balanced = y_train_balanced.sum()
    legitimate_count_balanced = len(y_train_balanced) - fraud_count_balanced
    scale_pos_weight = legitimate_count_balanced / fraud_count_balanced
    
    print(f"Scale pos weight: {scale_pos_weight:.2f}")
    
    # Train XGBoost with CONSERVATIVE parameters
    print("\n" + "-" * 70)
    print("TRAINING XGBOOST WITH CONSERVATIVE PARAMETERS")
    print("-" * 70)
    
    xgb_model = xgb.XGBClassifier(
        n_estimators=100,  # Reduced from 200
        max_depth=4,       # Reduced from 5
        learning_rate=0.1,  # Increased from 0.05
        scale_pos_weight=scale_pos_weight * 0.8,  # Slightly reduced weight
        min_child_weight=3,  # Increased from 1 to prevent overfitting
        gamma=0.2,         # Increased regularization
        subsample=0.7,     # Reduced from 0.8
        colsample_bytree=0.7,  # Reduced from 0.8
        reg_alpha=0.3,     # Increased L1 regularization
        reg_lambda=2.0,    # Increased L2 regularization
        objective='binary:logistic',
        random_state=42,
        eval_metric='auc'
    )
    
    xgb_model.fit(
        X_train_balanced, 
        y_train_balanced,
        eval_set=[(X_test_scaled, y_test)],
        verbose=False
    )
    
    # Predict on test set
    y_pred_proba = xgb_model.predict_proba(X_test_scaled)[:, 1]
    
    # Use multiple thresholds
    thresholds = [0.3, 0.4, 0.5, 0.6]
    
    print("\nXGBoost Performance at Different Thresholds:")
    print("-" * 70)
    
    best_threshold = 0.5
    best_f1 = 0
    
    for threshold in thresholds:
        y_pred = (y_pred_proba >= threshold).astype(int)
        print(f"\nThreshold = {threshold}:")
        report = classification_report(y_test, y_pred, 
                                      target_names=['Legitimate', 'Fraudulent'],
                                      output_dict=True)
        print(classification_report(y_test, y_pred, 
                                   target_names=['Legitimate', 'Fraudulent']))
        
        # Track best F1 score for fraudulent class
        fraud_f1 = report['Fraudulent']['f1-score']
        if fraud_f1 > best_f1:
            best_f1 = fraud_f1
            best_threshold = threshold
    
    print(f"\n✓ Best threshold: {best_threshold} (F1={best_f1:.3f})")
    
    roc_auc = roc_auc_score(y_test, y_pred_proba)
    print(f"ROC-AUC Score: {roc_auc:.4f}")
    
    # Train Isolation Forest ONLY on legitimate claims
    print("\n" + "-" * 70)
    print("TRAINING ISOLATION FOREST ON LEGITIMATE CLAIMS ONLY")
    print("-" * 70)
    
    # Get only legitimate claims from training set for anomaly detection
    X_train_legitimate = X_train_scaled[y_train == False]
    
    iso_forest = IsolationForest(
        n_estimators=100,
        contamination=0.1,  # Conservative contamination
        random_state=42,
        max_samples='auto'
    )
    
    iso_forest.fit(X_train_legitimate)  # Train only on legitimate claims
    
    anomaly_predictions = iso_forest.predict(X_test_scaled)
    anomaly_count = (anomaly_predictions == -1).sum()
    print(f"\nIsolation Forest detected {anomaly_count} anomalies in test set")
    
    # Ensemble predictions with CONSERVATIVE weights
    print("\n" + "-" * 70)
    print("ENSEMBLE MODEL (80% XGBoost, 20% Isolation Forest)")
    print("-" * 70)
    
    # Get anomaly scores
    anomaly_scores = iso_forest.decision_function(X_test_scaled)
    # Normalize: more negative = more anomalous
    anomaly_norm = np.clip((0 - anomaly_scores) / 0.5, 0, 1)
    
    # Conservative ensemble: Trust XGBoost more
    ensemble_proba = 0.8 * y_pred_proba + 0.2 * anomaly_norm
    ensemble_pred = (ensemble_proba >= best_threshold).astype(int)
    
    print("\nEnsemble Performance:")
    print(classification_report(y_test, ensemble_pred, 
                              target_names=['Legitimate', 'Fraudulent']))
    
    ensemble_auc = roc_auc_score(y_test, ensemble_proba)
    print(f"\nEnsemble ROC-AUC Score: {ensemble_auc:.4f}")
    
    # Feature importance
    print("\n" + "-" * 70)
    print("TOP 15 MOST IMPORTANT FEATURES")
    print("-" * 70)
    
    feature_importance = pd.DataFrame({
        'feature': available_features,
        'importance': xgb_model.feature_importances_
    }).sort_values('importance', ascending=False).head(15)
    
    print(feature_importance.to_string(index=False))
    
    # Save models
    print("\n" + "-" * 70)
    print("SAVING MODELS")
    print("-" * 70)
    
    model_dir = os.path.join(os.path.dirname(__file__), 'saved_models')
    os.makedirs(model_dir, exist_ok=True)
    
    joblib.dump(xgb_model, os.path.join(model_dir, 'fraud_detection_model.pkl'))
    joblib.dump(iso_forest, os.path.join(model_dir, 'isolation_forest_model.pkl'))
    joblib.dump(scaler, os.path.join(model_dir, 'fraud_scaler.pkl'))
    joblib.dump(available_features, os.path.join(model_dir, 'fraud_features.pkl'))
    joblib.dump({'optimal_threshold': best_threshold}, 
                os.path.join(model_dir, 'fraud_threshold.pkl'))
    
    print(f"✓ Saved all models with threshold {best_threshold}")
    
    # Update config file with new ensemble weights
    print("\n✓ Use ensemble weights: XGBoost=0.8, Isolation Forest=0.2")
    
    # Plot confusion matrix
    plt.figure(figsize=(8, 6))
    cm = confusion_matrix(y_test, ensemble_pred)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=['Legitimate', 'Fraudulent'],
                yticklabels=['Legitimate', 'Fraudulent'])
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.title(f'Confusion Matrix - Ensemble Model (threshold={best_threshold})')
    plt.tight_layout()
    plt.savefig(os.path.join(model_dir, 'fraud_confusion_matrix.png'), dpi=300)
    print(f"✓ Saved confusion matrix")
    
    print("\n" + "=" * 70)
    print("CONSERVATIVE FRAUD DETECTION MODEL TRAINING COMPLETE")
    print("=" * 70)
    print(f"\nKey Points:")
    print(f"  • Conservative parameters to prevent overfitting")
    print(f"  • SMOTE applied only to training data")
    print(f"  • Isolation Forest trained only on legitimate claims")
    print(f"  • Best threshold: {best_threshold}")
    print(f"  • ROC-AUC: {ensemble_auc:.1%}")
    print(f"  • Ensemble: 80% XGBoost, 20% Isolation Forest")


if __name__ == '__main__':
    train_conservative_model()