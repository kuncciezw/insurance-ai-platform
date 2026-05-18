"""
Claims Cost Estimation Model Training
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

import xgboost as xgb

# ---------------------------------------------------------------------------
# Django setup
# ---------------------------------------------------------------------------
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

# ---------------------------------------------------------------------------
# Project imports
# ---------------------------------------------------------------------------
from apps.fraud_detection.models import Policyholder, Vehicle, Policy, Claim
from ml_models.feature_engineering import FeatureEngineer
from ml_models.ml_config import (
    CLAIMS_ESTIMATOR_PATH,
    CLAIMS_SCALER_PATH,
    CLAIMS_FEATURES_PATH,
    CLAIMS_ESTIMATOR_PARAMS,
    CLAIMS_ESTIMATION_FEATURES,
)


# ===========================================================================
# Data loading
# ===========================================================================

def load_data_from_database() -> tuple:
    """Load the tables required for claims estimation from the database."""
    print("Loading data from database...")

    policyholders_df = pd.DataFrame(list(Policyholder.objects.all().values()))
    vehicles_df      = pd.DataFrame(list(Vehicle.objects.all().values()))
    policies_df      = pd.DataFrame(list(Policy.objects.all().values()))
    claims_df        = pd.DataFrame(
        list(
            Claim.objects.filter(
                claim_status__in=['APPROVED', 'REJECTED', 'UNDER_REVIEW']
            ).values()
        )
    )

    print(f"  ✓ {len(policyholders_df):,} policyholders")
    print(f"  ✓ {len(vehicles_df):,} vehicles")
    print(f"  ✓ {len(policies_df):,} policies")
    print(f"  ✓ {len(claims_df):,} claims")

    return policyholders_df, vehicles_df, policies_df, claims_df


# ===========================================================================
# Main training routine
# ===========================================================================

def train_claims_estimator() -> tuple | None:
    """End-to-end training pipeline for the claims cost estimation model."""

    print("=" * 70)
    print("CLAIMS COST ESTIMATION MODEL TRAINING")
    print("=" * 70 + "\n")

    # ------------------------------------------------------------------
    # 1. Load data
    # ------------------------------------------------------------------
    policyholders_df, vehicles_df, policies_df, claims_df = load_data_from_database()

    if len(claims_df) < 50:
        print("ERROR: Not enough claims data (need ≥ 50). Please generate data first.")
        return None

    # ------------------------------------------------------------------
    # 2. Feature engineering
    # ------------------------------------------------------------------
    print("\n" + "-" * 70)
    print("FEATURE ENGINEERING")
    print("-" * 70)

    feature_engineer = FeatureEngineer()
    df = feature_engineer.engineer_claims_estimation_features(
        claims_df, vehicles_df, policies_df
    )

    # ------------------------------------------------------------------
    # 3. Prepare X and y — dynamic feature list from ml_config
    # ------------------------------------------------------------------
    available_features = [f for f in CLAIMS_ESTIMATION_FEATURES if f in df.columns]
    missing = set(CLAIMS_ESTIMATION_FEATURES) - set(available_features)
    if missing:
        print(f"⚠️  Features in config but absent from DataFrame (skipped): {sorted(missing)}")

    X = df[available_features].copy()
    y = pd.to_numeric(df['approved_amount'], errors='coerce')

    # ------------------------------------------------------------------
    # 4. Robust NaN handling with .isna() masks (as required)
    # ------------------------------------------------------------------
    feature_nan_mask  = X.isna().any(axis=1)
    target_nan_mask   = y.isna()
    zero_target_mask  = (y <= 0)

    invalid_rows = feature_nan_mask | target_nan_mask | zero_target_mask

    if invalid_rows.any():
        print(f"\n  Dropping {invalid_rows.sum():,} rows with NaN features, "
              f"NaN target, or zero/negative approved_amount.")

    # Apply .isna()-based mask to keep only fully valid rows
    valid_mask = ~invalid_rows
    X = X.loc[valid_mask].reset_index(drop=True)
    y = y.loc[valid_mask].reset_index(drop=True)

    # Secondary safety fill for any remaining sparse NaNs
    X = X.fillna(0)

    if len(X) < 50:
        print("ERROR: Fewer than 50 valid samples remain after filtering. "
              "Please generate more approved/reviewed claims.")
        return None

    print(f"\nDataset after filtering:")
    print(f"  Samples            : {len(X):,}")
    print(f"  Features           : {len(available_features)}")
    print(f"\nApproved amount statistics:")
    print(f"  Mean               : ${y.mean():,.2f}")
    print(f"  Median             : ${y.median():,.2f}")
    print(f"  Std                : ${y.std():,.2f}")
    print(f"  Min                : ${y.min():,.2f}")
    print(f"  Max                : ${y.max():,.2f}")

    # ------------------------------------------------------------------
    # 5. Train / test split
    # ------------------------------------------------------------------
    params = CLAIMS_ESTIMATOR_PARAMS
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=params['test_size'],
        random_state=params['random_state'],
    )

    print(f"\n  Training set : {len(X_train):,} samples")
    print(f"  Test set     : {len(X_test):,} samples")

    # ------------------------------------------------------------------
    # 6. Scale features
    # ------------------------------------------------------------------
    print("\nScaling features...")
    X_train_scaled = feature_engineer.scale_features(X_train, fit=True)
    X_test_scaled  = feature_engineer.scale_features(X_test,  fit=False)

    # ------------------------------------------------------------------
    # 7. Train XGBoost regressor
    # ------------------------------------------------------------------
    print("\n" + "-" * 70)
    print("TRAINING XGBOOST REGRESSOR")
    print("-" * 70)

    model = xgb.XGBRegressor(**params['xgboost'])
    model.fit(
        X_train_scaled, y_train,
        eval_set=[(X_test_scaled, y_test)],
        verbose=False,
    )

    # ------------------------------------------------------------------
    # 8. Evaluate
    # ------------------------------------------------------------------
    y_pred_train = np.maximum(model.predict(X_train_scaled), 0)
    y_pred_test  = np.maximum(model.predict(X_test_scaled),  0)

    train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
    test_rmse  = np.sqrt(mean_squared_error(y_test,  y_pred_test))
    train_mae  = mean_absolute_error(y_train, y_pred_train)
    test_mae   = mean_absolute_error(y_test,  y_pred_test)
    train_r2   = r2_score(y_train, y_pred_train)
    test_r2    = r2_score(y_test,  y_pred_test)

    mape_test = np.mean(np.abs((y_test - y_pred_test) / y_test.replace(0, np.nan))) * 100

    within_10_pct = np.mean(np.abs((y_test - y_pred_test) / y_test.replace(0, np.nan)) <= 0.10) * 100
    within_20_pct = np.mean(np.abs((y_test - y_pred_test) / y_test.replace(0, np.nan)) <= 0.20) * 100

    print("\n" + "-" * 70)
    print("MODEL PERFORMANCE")
    print("-" * 70)
    print("\nTraining set:")
    print(f"  RMSE : ${train_rmse:,.2f}")
    print(f"  MAE  : ${train_mae:,.2f}")
    print(f"  R²   : {train_r2:.4f}")
    print("\nTest set:")
    print(f"  RMSE : ${test_rmse:,.2f}")
    print(f"  MAE  : ${test_mae:,.2f}")
    print(f"  R²   : {test_r2:.4f}")
    print(f"  MAPE : {mape_test:.2f}%")
    print("\nPrediction accuracy:")
    print(f"  Within ±10% : {within_10_pct:.1f}%")
    print(f"  Within ±20% : {within_20_pct:.1f}%")

    # ------------------------------------------------------------------
    # 9. Feature importance — column names from CLAIMS_ESTIMATION_FEATURES
    # ------------------------------------------------------------------
    print("\n" + "-" * 70)
    print("TOP FEATURE IMPORTANCES")
    print("-" * 70)

    fi_df = (
        pd.DataFrame({
            'feature':    available_features,          # dynamic — from config
            'importance': model.feature_importances_,
        })
        .sort_values('importance', ascending=False)
    )

    print(fi_df.head(10).to_string(index=False))

    # ------------------------------------------------------------------
    # 10. Save model artefacts
    # ------------------------------------------------------------------
    print("\n" + "-" * 70)
    print("SAVING MODELS")
    print("-" * 70)

    CLAIMS_ESTIMATOR_PATH.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(model,              CLAIMS_ESTIMATOR_PATH)
    feature_engineer.save_scaler(  CLAIMS_SCALER_PATH)
    joblib.dump(available_features, CLAIMS_FEATURES_PATH)

    print(f"  ✓ Model        → {CLAIMS_ESTIMATOR_PATH}")
    print(f"  ✓ Scaler       → {CLAIMS_SCALER_PATH}")
    print(f"  ✓ Feature list → {CLAIMS_FEATURES_PATH}")

    # ------------------------------------------------------------------
    # 11. Visualisations
    # ------------------------------------------------------------------
    print("\n" + "-" * 70)
    print("GENERATING VISUALISATIONS")
    print("-" * 70)

    plot_dir = CLAIMS_ESTIMATOR_PATH.parent

    # --- Feature importance ---
    plt.figure(figsize=(10, 8))
    top_fi = fi_df.head(min(12, len(fi_df)))
    plt.barh(range(len(top_fi)), top_fi['importance'])
    plt.yticks(range(len(top_fi)), top_fi['feature'])   # names from config
    plt.xlabel('Importance')
    plt.title('Top Features — Claims Cost Estimation')
    plt.tight_layout()
    fi_path = plot_dir / 'claims_feature_importance.png'
    plt.savefig(fi_path)
    plt.close()
    print(f"  ✓ Feature importance  → {fi_path}")

    # --- Predicted vs Actual ---
    plt.figure(figsize=(10, 6))
    plt.scatter(y_test, y_pred_test, alpha=0.5, edgecolors='k', linewidth=0.5)
    plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
    plt.xlabel('Actual Claim Amount ($)')
    plt.ylabel('Predicted Claim Amount ($)')
    plt.title('Claims Estimator: Predicted vs Actual')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    pred_path = plot_dir / 'claims_predictions.png'
    plt.savefig(pred_path)
    plt.close()
    print(f"  ✓ Predicted vs actual → {pred_path}")

    # --- Residuals ---
    residuals = y_test - y_pred_test
    plt.figure(figsize=(10, 6))
    plt.scatter(y_pred_test, residuals, alpha=0.5, edgecolors='k', linewidth=0.5)
    plt.axhline(y=0, color='r', linestyle='--', lw=2)
    plt.xlabel('Predicted Claim Amount ($)')
    plt.ylabel('Residuals ($)')
    plt.title('Residuals Plot')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    res_path = plot_dir / 'claims_residuals.png'
    plt.savefig(res_path)
    plt.close()
    print(f"  ✓ Residuals           → {res_path}")

    # --- Error distribution ---
    pct_errors = np.abs((y_test - y_pred_test) / y_test.replace(0, np.nan)) * 100
    plt.figure(figsize=(10, 6))
    plt.hist(pct_errors.dropna(), bins=50, edgecolor='black', alpha=0.7)
    plt.axvline(x=10, color='r',      linestyle='--', label='±10% threshold')
    plt.axvline(x=20, color='orange', linestyle='--', label='±20% threshold')
    plt.xlabel('Absolute Percentage Error (%)')
    plt.ylabel('Frequency')
    plt.title('Distribution of Prediction Errors')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    err_path = plot_dir / 'claims_error_distribution.png'
    plt.savefig(err_path)
    plt.close()
    print(f"  ✓ Error distribution  → {err_path}")

    # --- By severity (uses dynamically-encoded severity_encoded) ---
    if 'severity_encoded' in X_test.columns:
        severity_map = {0: 'Minor', 1: 'Moderate', 2: 'Major', 3: 'Critical'}
        sev_df = pd.DataFrame({
            'actual':    y_test.values,
            'predicted': y_pred_test,
            'severity':  X_test['severity_encoded'].values,
        })
        sev_df['severity_label'] = sev_df['severity'].map(severity_map)

        plt.figure(figsize=(12, 6))
        for label in ['Minor', 'Moderate', 'Major', 'Critical']:
            sub = sev_df[sev_df['severity_label'] == label]
            if not sub.empty:
                plt.scatter(sub['actual'], sub['predicted'], label=label, alpha=0.6, s=50)

        plt.plot(
            [y_test.min(), y_test.max()],
            [y_test.min(), y_test.max()],
            'k--', lw=2,
        )
        plt.xlabel('Actual Claim Amount ($)')
        plt.ylabel('Predicted Claim Amount ($)')
        plt.title('Predictions by Claim Severity')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        sev_path = plot_dir / 'claims_by_severity.png'
        plt.savefig(sev_path)
        plt.close()
        print(f"  ✓ Severity analysis   → {sev_path}")

    # ------------------------------------------------------------------
    # 12. Summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("CLAIMS COST ESTIMATION MODEL TRAINING COMPLETE")
    print("=" * 70)
    print("\n📊 Model summary:")
    print(f"   Test RMSE              : ${test_rmse:,.2f}")
    print(f"   Test MAE               : ${test_mae:,.2f}")
    print(f"   Test R²                : {test_r2:.4f}")
    print(f"   Accuracy within ±10%   : {within_10_pct:.1f}%")
    print(f"   Accuracy within ±20%   : {within_20_pct:.1f}%")
    print("\n✅ Model saved and ready for use!")

    return model, feature_engineer


if __name__ == '__main__':
    train_claims_estimator()