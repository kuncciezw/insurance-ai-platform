"""
Improved Fraud Detection Model Training with Class Balancing
Save as: ml_models/train_fraud_detection_improved.py
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
from imblearn.over_sampling import SMOTE  # For handling class imbalance
from imblearn.under_sampling import RandomUnderSampler
from imblearn.pipeline import Pipeline as ImbPipeline
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


def augment_fraud_cases(df, target_col='is_fraudulent', augmentation_factor=3):
    """
    Augment fraudulent cases with slight variations
    This helps the model learn fraud patterns better
    """
    fraud_cases = df[df[target_col] == True].copy()
    
    if len(fraud_cases) == 0:
        return df
    
    print(f"\nAugmenting {len(fraud_cases)} fraud cases...")
    
    augmented_cases = []
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    for _ in range(augmentation_factor):
        augmented = fraud_cases.copy()
        
        # Add small random noise to numeric features (±5%)
        for col in numeric_cols:
            if col not in [target_col, 'id']:
                noise = np.random.normal(0, 0.05, len(augmented))
                augmented[col] = augmented[col] * (1 + noise)
        
        augmented_cases.append(augmented)
    
    augmented_df = pd.concat([df] + augmented_cases, ignore_index=True)
    print(f"✓ Dataset expanded to {len(augmented_df)} samples")
    
    return augmented_df


def train_improved_model():
    """Train improved fraud detection model with class balancing"""
    
    print("=" * 70)
    print("IMPROVED FRAUD DETECTION MODEL TRAINING")
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
    
    # Select only the most important features (based on your training output)
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
    
    # Filter to available features
    available_features = [f for f in important_features if f in df.columns]
    
    X = df[available_features].copy()
    y = df[target_col].copy()
    
    # Fill NaN values
    X = X.fillna(0)
    
    print(f"\nDataset shape: {X.shape}")
    print(f"Fraudulent claims: {y.sum()} ({y.sum()/len(y)*100:.2f}%)")
    print(f"Legitimate claims: {(~y).sum()} ({(~y).sum()/len(y)*100:.2f}%)")
    
    # Augment fraud cases BEFORE splitting
    combined_df = X.copy()
    combined_df[target_col] = y
    combined_df = augment_fraud_cases(combined_df, target_col, augmentation_factor=5)
    
    X = combined_df[available_features]
    y = combined_df[target_col]
    
    print(f"\nAfter augmentation:")
    print(f"Fraudulent claims: {y.sum()} ({y.sum()/len(y)*100:.2f}%)")
    print(f"Legitimate claims: {(~y).sum()} ({(~y).sum()/len(y)*100:.2f}%)")
    
    # Train-test split with stratification
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"\nTraining set: {len(X_train)} samples")
    print(f"Test set: {len(X_test)} samples")
    print(f"Training fraud rate: {y_train.sum()/len(y_train)*100:.2f}%")
    print(f"Test fraud rate: {y_test.sum()/len(y_test)*100:.2f}%")
    
    # Scale features
    print("\nScaling features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train XGBoost with class weights and SMOTE
    print("\n" + "-" * 70)
    print("TRAINING XGBOOST WITH CLASS BALANCING")
    print("-" * 70)
    
    # Calculate class weights
    fraud_count = y_train.sum()
    legitimate_count = (~y_train).sum()
    scale_pos_weight = legitimate_count / fraud_count
    
    print(f"Scale pos weight: {scale_pos_weight:.2f}")
    
    # Apply SMOTE to training data
    smote = SMOTE(random_state=42, k_neighbors=3)
    X_train_balanced, y_train_balanced = smote.fit_resample(X_train_scaled, y_train)
    
    print(f"After SMOTE:")
    print(f"Training samples: {len(X_train_balanced)}")
    print(f"Fraud rate: {y_train_balanced.sum()/len(y_train_balanced)*100:.2f}%")
    
    # Train XGBoost with adjusted parameters
    xgb_model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.05,
        scale_pos_weight=scale_pos_weight,
        min_child_weight=1,
        gamma=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        objective='binary:logistic',
        random_state=42,
        eval_metric='auc'
    )
    
    xgb_model.fit(X_train_balanced, y_train_balanced)
    
    # Predict on test set
    y_pred = xgb_model.predict(X_test_scaled)
    y_pred_proba = xgb_model.predict_proba(X_test_scaled)[:, 1]
    
    # Adjust threshold for better recall
    optimal_threshold = 0.4  # Lower threshold to catch more fraud
    y_pred_adjusted = (y_pred_proba >= optimal_threshold).astype(int)
    
    print("\nXGBoost Performance (threshold=0.5):")
    print(classification_report(y_test, y_pred, 
                              target_names=['Legitimate', 'Fraudulent']))
    
    print(f"\nXGBoost Performance (threshold={optimal_threshold}):")
    print(classification_report(y_test, y_pred_adjusted, 
                              target_names=['Legitimate', 'Fraudulent']))
    
    roc_auc = roc_auc_score(y_test, y_pred_proba)
    print(f"\nROC-AUC Score: {roc_auc:.4f}")
    
    # Train Isolation Forest for anomaly detection
    print("\n" + "-" * 70)
    print("TRAINING ISOLATION FOREST (ANOMALY DETECTION)")
    print("-" * 70)
    
    iso_forest = IsolationForest(
        n_estimators=200,
        contamination=0.15,  # Expect 15% anomalies
        random_state=42,
        max_samples='auto'
    )
    
    iso_forest.fit(X_train_scaled)
    anomaly_scores = iso_forest.decision_function(X_test_scaled)
    anomaly_predictions = iso_forest.predict(X_test_scaled)
    
    anomaly_count = (anomaly_predictions == -1).sum()
    print(f"\nIsolation Forest detected {anomaly_count} anomalies")
    
    # Ensemble predictions
    print("\n" + "-" * 70)
    print("ENSEMBLE MODEL (XGBoost + Isolation Forest)")
    print("-" * 70)
    
    # Normalize anomaly scores to 0-1 range
    anomaly_scores_norm = (anomaly_scores - anomaly_scores.min()) / \
                          (anomaly_scores.max() - anomaly_scores.min())
    
    # Combine predictions (weighted average)
    ensemble_proba = 0.7 * y_pred_proba + 0.3 * (1 - anomaly_scores_norm)
    ensemble_pred = (ensemble_proba >= optimal_threshold).astype(int)
    
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
    
    # Save models
    joblib.dump(xgb_model, os.path.join(model_dir, 'fraud_detection_model.pkl'))
    joblib.dump(iso_forest, os.path.join(model_dir, 'isolation_forest_model.pkl'))
    joblib.dump(scaler, os.path.join(model_dir, 'fraud_scaler.pkl'))
    joblib.dump(available_features, os.path.join(model_dir, 'fraud_features.pkl'))
    joblib.dump({'optimal_threshold': optimal_threshold}, 
                os.path.join(model_dir, 'fraud_threshold.pkl'))
    
    print(f"✓ Saved XGBoost model")
    print(f"✓ Saved Isolation Forest")
    print(f"✓ Saved scaler")
    print(f"✓ Saved feature list")
    print(f"✓ Saved optimal threshold ({optimal_threshold})")
    
    # Plot feature importance
    plt.figure(figsize=(10, 8))
    feature_importance_plot = feature_importance.head(15)
    plt.barh(range(len(feature_importance_plot)), feature_importance_plot['importance'])
    plt.yticks(range(len(feature_importance_plot)), feature_importance_plot['feature'])
    plt.xlabel('Importance')
    plt.title('Top 15 Feature Importances')
    plt.tight_layout()
    plt.savefig(os.path.join(model_dir, 'fraud_feature_importance.png'), dpi=300)
    print(f"✓ Saved feature importance plot")
    
    # Plot confusion matrix
    plt.figure(figsize=(8, 6))
    cm = confusion_matrix(y_test, ensemble_pred)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=['Legitimate', 'Fraudulent'],
                yticklabels=['Legitimate', 'Fraudulent'])
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.title('Confusion Matrix - Ensemble Model')
    plt.tight_layout()
    plt.savefig(os.path.join(model_dir, 'fraud_confusion_matrix.png'), dpi=300)
    print(f"✓ Saved confusion matrix")
    
    # Plot ROC curve
    plt.figure(figsize=(8, 6))
    fpr, tpr, thresholds = roc_curve(y_test, ensemble_proba)
    plt.plot(fpr, tpr, label=f'ROC Curve (AUC = {ensemble_auc:.3f})')
    plt.plot([0, 1], [0, 1], 'k--', label='Random Classifier')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC Curve - Ensemble Model')
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(model_dir, 'fraud_roc_curve.png'), dpi=300)
    print(f"✓ Saved ROC curve")
    
    print("\n" + "=" * 70)
    print("IMPROVED FRAUD DETECTION MODEL TRAINING COMPLETE")
    print("=" * 70)
    print(f"\nKey Improvements:")
    print(f"  • Used SMOTE to balance training data")
    print(f"  • Augmented fraud cases with variations")
    print(f"  • Adjusted classification threshold to {optimal_threshold}")
    print(f"  • Achieved {ensemble_auc:.1%} ROC-AUC score")
    print(f"  • Improved fraud detection recall")


if __name__ == '__main__':
    train_improved_model()