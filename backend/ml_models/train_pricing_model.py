"""
Train Dynamic Pricing Model
Predicts insurance premium based on risk factors
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

from apps.fraud_detection.models import Policyholder, Vehicle, Policy
from ml_models.feature_engineering import FeatureEngineer
from ml_models.ml_config import (
    PRICING_MODEL_PATH, PRICING_SCALER_PATH, PRICING_FEATURES_PATH,
    PRICING_MODEL_PARAMS, PRICING_FEATURES
)


def load_data_from_database():
    """Load data from Django database"""
    print("Loading data from database...")
    
    policyholders = Policyholder.objects.all().values()
    vehicles = Vehicle.objects.all().values()
    policies = Policy.objects.filter(status='ACTIVE').values()
    
    policyholders_df = pd.DataFrame(policyholders)
    vehicles_df = pd.DataFrame(vehicles)
    policies_df = pd.DataFrame(policies)
    
    print(f"✓ Loaded {len(policyholders_df)} policyholders")
    print(f"✓ Loaded {len(vehicles_df)} vehicles")
    print(f"✓ Loaded {len(policies_df)} active policies")
    
    return policyholders_df, vehicles_df, policies_df


def train_pricing_model():
    """Train dynamic pricing model"""
    
    print("="*70)
    print("DYNAMIC PRICING MODEL TRAINING")
    print("="*70 + "\n")
    
    # Load data
    policyholders_df, vehicles_df, policies_df = load_data_from_database()
    
    if len(policies_df) < 50:
        print("ERROR: Not enough policy data. Please generate data first.")
        return
    
    # Feature engineering
    print("\n" + "-"*70)
    print("FEATURE ENGINEERING")
    print("-"*70)
    feature_engineer = FeatureEngineer()
    df = feature_engineer.engineer_pricing_features(
        policyholders_df, vehicles_df, policies_df
    )
    
    # Prepare features and target
    X = df[PRICING_FEATURES].copy()
    y = pd.to_numeric(df['premium_amount'], errors='coerce')
    
    # Remove any NaN values in target
    valid_mask = ~y.isna()
    X = X[valid_mask]
    y = y[valid_mask]
    
    print(f"\nDataset shape: {X.shape}")
    print(f"Premium statistics:")
    print(f"  Mean: ${y.mean():.2f}")
    print(f"  Median: ${y.median():.2f}")
    print(f"  Std: ${y.std():.2f}")
    print(f"  Min: ${y.min():.2f}")
    print(f"  Max: ${y.max():.2f}")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=PRICING_MODEL_PARAMS['test_size'],
        random_state=PRICING_MODEL_PARAMS['random_state']
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
    
    model = xgb.XGBRegressor(**PRICING_MODEL_PARAMS['xgboost'])
    model.fit(
        X_train_scaled, y_train,
        eval_set=[(X_test_scaled, y_test)],
        verbose=False
    )
    
    # Predictions
    y_pred_train = model.predict(X_train_scaled)
    y_pred_test = model.predict(X_test_scaled)
    
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
    
    # Feature importance
    print("\n" + "-"*70)
    print("TOP 10 MOST IMPORTANT FEATURES")
    print("-"*70)
    
    feature_importance = pd.DataFrame({
        'feature': PRICING_FEATURES,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print(feature_importance.head(10).to_string(index=False))
    
    # Save model
    print("\n" + "-"*70)
    print("SAVING MODEL")
    print("-"*70)
    
    joblib.dump(model, PRICING_MODEL_PATH)
    print(f"✓ Saved model to {PRICING_MODEL_PATH}")
    
    feature_engineer.save_scaler(PRICING_SCALER_PATH)
    joblib.dump(PRICING_FEATURES, PRICING_FEATURES_PATH)
    print(f"✓ Saved feature list to {PRICING_FEATURES_PATH}")
    
    # Save visualizations
    # Feature importance
    plt.figure(figsize=(10, 8))
    top_features = feature_importance.head(15)
    plt.barh(range(len(top_features)), top_features['importance'])
    plt.yticks(range(len(top_features)), top_features['feature'])
    plt.xlabel('Importance')
    plt.title('Top 15 Features for Premium Pricing')
    plt.tight_layout()
    plot_path = PRICING_MODEL_PATH.parent / 'pricing_feature_importance.png'
    plt.savefig(plot_path)
    print(f"✓ Saved feature importance plot to {plot_path}")
    plt.close()
    
    # Prediction vs Actual
    plt.figure(figsize=(10, 6))
    plt.scatter(y_test, y_pred_test, alpha=0.5)
    plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
    plt.xlabel('Actual Premium ($)')
    plt.ylabel('Predicted Premium ($)')
    plt.title('Pricing Model: Predicted vs Actual')
    plt.tight_layout()
    pred_plot_path = PRICING_MODEL_PATH.parent / 'pricing_predictions.png'
    plt.savefig(pred_plot_path)
    print(f"✓ Saved predictions plot to {pred_plot_path}")
    plt.close()
    
    # Residuals plot
    residuals = y_test - y_pred_test
    plt.figure(figsize=(10, 6))
    plt.scatter(y_pred_test, residuals, alpha=0.5)
    plt.axhline(y=0, color='r', linestyle='--', lw=2)
    plt.xlabel('Predicted Premium ($)')
    plt.ylabel('Residuals ($)')
    plt.title('Residuals Plot')
    plt.tight_layout()
    residuals_path = PRICING_MODEL_PATH.parent / 'pricing_residuals.png'
    plt.savefig(residuals_path)
    print(f"✓ Saved residuals plot to {residuals_path}")
    plt.close()
    
    print("\n" + "="*70)
    print("PRICING MODEL TRAINING COMPLETE")
    print("="*70)
    
    return model, feature_engineer


if __name__ == '__main__':
    train_pricing_model()