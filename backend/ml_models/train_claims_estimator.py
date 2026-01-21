"""
Train Claims Cost Estimation Model
Predicts estimated settlement amount for insurance claims
"""

import os
import sys
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import xgboost as xgb
import matplotlib.pyplot as plt
import seaborn as sns

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from apps.fraud_detection.models import Policyholder, Vehicle, Policy, Claim
from ml_models.feature_engineering import FeatureEngineer
from ml_models.ml_config import (
    CLAIMS_ESTIMATOR_PATH, CLAIMS_SCALER_PATH, CLAIMS_FEATURES_PATH,
    CLAIMS_ESTIMATOR_PARAMS, CLAIMS_ESTIMATION_FEATURES
)


def load_data_from_database():
    """Load data from Django database"""
    print("Loading data from database...")
    
    policyholders = Policyholder.objects.all().values()
    vehicles = Vehicle.objects.all().values()
    policies = Policy.objects.all().values()
    claims = Claim.objects.filter(claim_status__in=['APPROVED', 'REJECTED', 'UNDER_REVIEW']).values()
    
    policyholders_df = pd.DataFrame(policyholders)
    vehicles_df = pd.DataFrame(vehicles)
    policies_df = pd.DataFrame(policies)
    claims_df = pd.DataFrame(claims)
    
    print(f"✓ Loaded {len(policyholders_df)} policyholders")
    print(f"✓ Loaded {len(vehicles_df)} vehicles")
    print(f"✓ Loaded {len(policies_df)} policies")
    print(f"✓ Loaded {len(claims_df)} claims")
    
    return policyholders_df, vehicles_df, policies_df, claims_df


def train_claims_estimator():
    """Train claims cost estimation model"""
    
    print("="*70)
    print("CLAIMS COST ESTIMATION MODEL TRAINING")
    print("="*70 + "\n")
    
    # Load data
    policyholders_df, vehicles_df, policies_df, claims_df = load_data_from_database()
    
    if len(claims_df) < 50:
        print("ERROR: Not enough claims data. Please generate data first.")
        return
    
    # Feature engineering
    print("\n" + "-"*70)
    print("FEATURE ENGINEERING")
    print("-"*70)
    feature_engineer = FeatureEngineer()
    df = feature_engineer.engineer_claims_estimation_features(
        claims_df, vehicles_df, policies_df
    )
    
    # Prepare features and target
    X = df[CLAIMS_ESTIMATION_FEATURES].copy()
    y = pd.to_numeric(df['approved_amount'], errors='coerce')
    
    # Remove any NaN values in target and filter out zero values
    valid_mask = ~y.isna() & (y > 0)
    X = X[valid_mask]
    y = y[valid_mask]
    
    print(f"\nDataset shape: {X.shape}")
    print(f"Claim amount statistics:")
    print(f"  Mean: ${y.mean():.2f}")
    print(f"  Median: ${y.median():.2f}")
    print(f"  Std: ${y.std():.2f}")
    print(f"  Min: ${y.min():.2f}")
    print(f"  Max: ${y.max():.2f}")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=CLAIMS_ESTIMATOR_PARAMS['test_size'],
        random_state=CLAIMS_ESTIMATOR_PARAMS['random_state']
    )
    
    print(f"\nTraining set: {len(X_train)} samples")
    print(f"Test set: {len(X_test)} samples")
    
    # Scale features
    print("\nScaling features...")
    X_train_scaled = feature_engineer.scale_features(X_train, fit=True)
    X_test_scaled = feature_engineer.scale_features(X_test, fit=False)
    
    # Train model
    print("\n" + "-"*70)
    print("TRAINING XGBOOST REGRESSOR")
    print("-"*70)
    
    model = xgb.XGBRegressor(**CLAIMS_ESTIMATOR_PARAMS['xgboost'])
    model.fit(
        X_train_scaled, y_train,
        eval_set=[(X_test_scaled, y_test)],
        verbose=False
    )
    
    # Predictions
    y_pred_train = model.predict(X_train_scaled)
    y_pred_test = model.predict(X_test_scaled)
    
    # Ensure predictions are non-negative
    y_pred_train = np.maximum(y_pred_train, 0)
    y_pred_test = np.maximum(y_pred_test, 0)
    
    # Evaluate
    print("\n" + "-"*70)
    print("MODEL PERFORMANCE")
    print("-"*70)
    
    train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
    test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
    train_mae = mean_absolute_error(y_train, y_pred_train)
    test_mae = mean_absolute_error(y_test, y_pred_test)
    train_r2 = r2_score(y_train, y_pred_train)
    test_r2 = r2_score(y_test, y_pred_test)
    
    print("\nTraining Set:")
    print(f"  RMSE: ${train_rmse:.2f}")
    print(f"  MAE: ${train_mae:.2f}")
    print(f"  R² Score: {train_r2:.4f}")
    
    print("\nTest Set:")
    print(f"  RMSE: ${test_rmse:.2f}")
    print(f"  MAE: ${test_mae:.2f}")
    print(f"  R² Score: {test_r2:.4f}")
    
    # Calculate percentage error
    mape_test = np.mean(np.abs((y_test - y_pred_test) / y_test)) * 100
    print(f"  MAPE: {mape_test:.2f}%")
    
    # Accuracy within tolerance bands
    within_10_pct = np.mean(np.abs((y_test - y_pred_test) / y_test) <= 0.10) * 100
    within_20_pct = np.mean(np.abs((y_test - y_pred_test) / y_test) <= 0.20) * 100
    print(f"\nPrediction Accuracy:")
    print(f"  Within ±10%: {within_10_pct:.1f}%")
    print(f"  Within ±20%: {within_20_pct:.1f}%")
    
    # Feature importance
    print("\n" + "-"*70)
    print("TOP 10 MOST IMPORTANT FEATURES")
    print("-"*70)
    
    feature_importance = pd.DataFrame({
        'feature': CLAIMS_ESTIMATION_FEATURES,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print(feature_importance.head(10).to_string(index=False))
    
    # Save model
    print("\n" + "-"*70)
    print("SAVING MODEL")
    print("-"*70)
    
    joblib.dump(model, CLAIMS_ESTIMATOR_PATH)
    print(f"✓ Saved model to {CLAIMS_ESTIMATOR_PATH}")
    
    feature_engineer.save_scaler(CLAIMS_SCALER_PATH)
    joblib.dump(CLAIMS_ESTIMATION_FEATURES, CLAIMS_FEATURES_PATH)
    print(f"✓ Saved feature list to {CLAIMS_FEATURES_PATH}")
    
    # Save visualizations
    print("\n" + "-"*70)
    print("GENERATING VISUALIZATIONS")
    print("-"*70)
    
    # 1. Feature importance
    plt.figure(figsize=(10, 8))
    top_features = feature_importance.head(12)
    plt.barh(range(len(top_features)), top_features['importance'])
    plt.yticks(range(len(top_features)), top_features['feature'])
    plt.xlabel('Importance')
    plt.title('Top Features for Claims Cost Estimation')
    plt.tight_layout()
    plot_path = CLAIMS_ESTIMATOR_PATH.parent / 'claims_feature_importance.png'
    plt.savefig(plot_path)
    print(f"✓ Saved feature importance plot to {plot_path}")
    plt.close()
    
    # 2. Prediction vs Actual
    plt.figure(figsize=(10, 6))
    plt.scatter(y_test, y_pred_test, alpha=0.5, edgecolors='k', linewidth=0.5)
    plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
    plt.xlabel('Actual Claim Amount ($)')
    plt.ylabel('Predicted Claim Amount ($)')
    plt.title('Claims Estimator: Predicted vs Actual')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    pred_plot_path = CLAIMS_ESTIMATOR_PATH.parent / 'claims_predictions.png'
    plt.savefig(pred_plot_path)
    print(f"✓ Saved predictions plot to {pred_plot_path}")
    plt.close()
    
    # 3. Residuals plot
    residuals = y_test - y_pred_test
    plt.figure(figsize=(10, 6))
    plt.scatter(y_pred_test, residuals, alpha=0.5, edgecolors='k', linewidth=0.5)
    plt.axhline(y=0, color='r', linestyle='--', lw=2)
    plt.xlabel('Predicted Claim Amount ($)')
    plt.ylabel('Residuals ($)')
    plt.title('Residuals Plot')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    residuals_path = CLAIMS_ESTIMATOR_PATH.parent / 'claims_residuals.png'
    plt.savefig(residuals_path)
    print(f"✓ Saved residuals plot to {residuals_path}")
    plt.close()
    
    # 4. Error distribution
    plt.figure(figsize=(10, 6))
    percentage_errors = np.abs((y_test - y_pred_test) / y_test) * 100
    plt.hist(percentage_errors, bins=50, edgecolor='black', alpha=0.7)
    plt.xlabel('Absolute Percentage Error (%)')
    plt.ylabel('Frequency')
    plt.title('Distribution of Prediction Errors')
    plt.axvline(x=10, color='r', linestyle='--', label='±10% threshold')
    plt.axvline(x=20, color='orange', linestyle='--', label='±20% threshold')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    error_dist_path = CLAIMS_ESTIMATOR_PATH.parent / 'claims_error_distribution.png'
    plt.savefig(error_dist_path)
    print(f"✓ Saved error distribution plot to {error_dist_path}")
    plt.close()
    
    # 5. Claims by severity
    severity_map = {0: 'Minor', 1: 'Moderate', 2: 'Severe', 3: 'Critical'}
    test_data = pd.DataFrame({
        'actual': y_test,
        'predicted': y_pred_test,
        'severity': X_test['severity_encoded'].map(severity_map)
    })
    
    plt.figure(figsize=(12, 6))
    severity_order = ['Minor', 'Moderate', 'Severe', 'Critical']
    for severity in severity_order:
        severity_data = test_data[test_data['severity'] == severity]
        if len(severity_data) > 0:
            plt.scatter(severity_data['actual'], severity_data['predicted'], 
                       label=severity, alpha=0.6, s=50)
    
    plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'k--', lw=2)
    plt.xlabel('Actual Claim Amount ($)')
    plt.ylabel('Predicted Claim Amount ($)')
    plt.title('Predictions by Claim Severity')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    severity_plot_path = CLAIMS_ESTIMATOR_PATH.parent / 'claims_by_severity.png'
    plt.savefig(severity_plot_path)
    print(f"✓ Saved severity analysis plot to {severity_plot_path}")
    plt.close()
    
    print("\n" + "="*70)
    print("CLAIMS COST ESTIMATION MODEL TRAINING COMPLETE")
    print("="*70)
    print("\n📊 Model Summary:")
    print(f"   • Test RMSE: ${test_rmse:.2f}")
    print(f"   • Test MAE: ${test_mae:.2f}")
    print(f"   • Test R²: {test_r2:.4f}")
    print(f"   • Accuracy within ±10%: {within_10_pct:.1f}%")
    print(f"   • Accuracy within ±20%: {within_20_pct:.1f}%")
    print(f"\n✅ Model saved and ready for use!")
    
    return model, feature_engineer


if __name__ == '__main__':
    train_claims_estimator()