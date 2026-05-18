"""
Fraud Detection Model Training
"""

import os
import sys
import django
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')          # Non-interactive backend — safe for server environments
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# ---------------------------------------------------------------------------
# Django setup
# ---------------------------------------------------------------------------
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# ---------------------------------------------------------------------------
# Third-party imports
# ---------------------------------------------------------------------------
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    roc_curve,
)
from sklearn.ensemble import IsolationForest
from imblearn.over_sampling import SMOTE
import xgboost as xgb
import joblib

# ---------------------------------------------------------------------------
# Project imports
# ---------------------------------------------------------------------------
from apps.fraud_detection.models import Claim, Policy, Policyholder, Vehicle
from ml_models.feature_engineering import FeatureEngineer
from ml_models.ml_config import (
    FRAUD_DETECTION_FEATURES,
    FRAUD_DETECTION_PARAMS,
    ENSEMBLE_WEIGHTS,
    FRAUD_RISK_THRESHOLDS,
    FRAUD_DETECTION_MODEL_PATH,
    FRAUD_ISOLATION_FOREST_PATH,
    FRAUD_SCALER_PATH,
    FRAUD_FEATURES_PATH,
    FRAUD_THRESHOLD_PATH,
)


# ===========================================================================
# Data loading
# ===========================================================================

def load_data() -> tuple:
    """Pull all required tables from the database and return as DataFrames."""
    print("\nLoading data from database...")

    claims_df        = pd.DataFrame(list(Claim.objects.all().values()))
    policyholders_df = pd.DataFrame(list(Policyholder.objects.all().values()))
    vehicles_df      = pd.DataFrame(list(Vehicle.objects.all().values()))
    policies_df      = pd.DataFrame(list(Policy.objects.all().values()))

    print(f"  ✓ {len(claims_df):,} claims")
    print(f"  ✓ {len(policyholders_df):,} policyholders")
    print(f"  ✓ {len(vehicles_df):,} vehicles")
    print(f"  ✓ {len(policies_df):,} policies")

    return claims_df, policyholders_df, vehicles_df, policies_df


# ===========================================================================
# Helper: choose best decision threshold
# ===========================================================================

def _select_best_threshold(
    y_true: np.ndarray,
    y_proba: np.ndarray,
    candidates: list | None = None,
) -> tuple[float, float]:
    """
    Evaluate candidate thresholds and return (best_threshold, best_f1)
    where best_f1 is the F1 score for the *Fraudulent* class.
    """
    if candidates is None:
        candidates = [0.3, 0.4, 0.5, 0.6]

    best_threshold, best_f1 = candidates[0], 0.0

    print("\nThreshold search:")
    print("-" * 60)
    for t in candidates:
        y_pred = (y_proba >= t).astype(int)
        report = classification_report(
            y_true, y_pred,
            target_names=['Legitimate', 'Fraudulent'],
            output_dict=True,
            zero_division=0,
        )
        fraud_f1 = report['Fraudulent']['f1-score']
        fraud_prec = report['Fraudulent']['precision']
        fraud_rec  = report['Fraudulent']['recall']
        print(
            f"  t={t:.2f}  |  F1={fraud_f1:.3f}  "
            f"Prec={fraud_prec:.3f}  Rec={fraud_rec:.3f}"
        )
        if fraud_f1 > best_f1:
            best_f1, best_threshold = fraud_f1, t

    return best_threshold, best_f1


# ===========================================================================
# Main training routine
# ===========================================================================

def train_fraud_detection_model() -> None:
    """End-to-end training pipeline for the fraud detection ensemble."""

    print("=" * 70)
    print("FRAUD DETECTION MODEL TRAINING")
    print("=" * 70)

    # ------------------------------------------------------------------
    # 1. Load & engineer features
    # ------------------------------------------------------------------
    claims_df, policyholders_df, vehicles_df, policies_df = load_data()

    print("\n" + "-" * 70)
    print("FEATURE ENGINEERING")
    print("-" * 70)

    feature_engineer = FeatureEngineer()
    df = feature_engineer.engineer_fraud_detection_features(
        claims_df, policyholders_df, vehicles_df, policies_df
    )

    # ------------------------------------------------------------------
    # 2. Select features dynamically from ml_config
    # ------------------------------------------------------------------
    target_col = 'is_fraudulent'
    available_features = [f for f in FRAUD_DETECTION_FEATURES if f in df.columns]

    missing = set(FRAUD_DETECTION_FEATURES) - set(available_features)
    if missing:
        print(f"⚠️  Features in config but absent from DataFrame (skipped): {sorted(missing)}")

    X = df[available_features].copy().fillna(0)
    y = df[target_col].copy()

    print(f"\nDataset summary:")
    print(f"  Total samples      : {len(X):,}")
    print(f"  Fraudulent claims  : {y.sum():,}  ({y.mean()*100:.2f} %)")
    print(f"  Legitimate claims  : {(~y).sum():,}  ({(1-y.mean())*100:.2f} %)")
    print(f"  Features used      : {len(available_features)}")

    if y.sum() < 5:
        raise RuntimeError(
            "Fewer than 5 fraud cases found — cannot train a meaningful model. "
            "Please generate more data before training."
        )

    # ------------------------------------------------------------------
    # 3. Train / test split  ← MUST happen before SMOTE
    # ------------------------------------------------------------------
    params = FRAUD_DETECTION_PARAMS
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=params['test_size'],
        random_state=params['random_state'],
        stratify=y,
    )

    print(f"\nSplit (before SMOTE):")
    print(f"  Train : {len(X_train):,}  (fraud={y_train.sum():,})")
    print(f"  Test  : {len(X_test):,}   (fraud={y_test.sum():,})")

    # ------------------------------------------------------------------
    # 4. Scale features — fit ONLY on training data
    # ------------------------------------------------------------------
    print("\nScaling features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled  = scaler.transform(X_test)

    # ------------------------------------------------------------------
    # 5. SMOTE — applied ONLY to the scaled training set
    #    (leakage fix: test data is never seen during resampling)
    # ------------------------------------------------------------------
    fraud_in_train = int(y_train.sum())
    k_neighbors    = min(
        params.get('smote_k_neighbors', 3),
        max(1, fraud_in_train - 1),
    )
    sampling_strategy = params.get('sampling_strategy', 0.5)

    if params.get('use_smote', True):
        print(f"\nApplying SMOTE (k_neighbors={k_neighbors}, "
              f"sampling_strategy={sampling_strategy})...")
        smote = SMOTE(
            random_state=params['random_state'],
            k_neighbors=k_neighbors,
            sampling_strategy=sampling_strategy,
        )
        X_train_balanced, y_train_balanced = smote.fit_resample(X_train_scaled, y_train)
        print(f"  After SMOTE — train: {len(X_train_balanced):,}  "
              f"(fraud={y_train_balanced.sum():,})")
    else:
        print("\nSMOTE disabled — using original class distribution.")
        X_train_balanced, y_train_balanced = X_train_scaled, y_train

    # ------------------------------------------------------------------
    # 6. XGBoost — dynamic hyperparameters from ml_config
    # ------------------------------------------------------------------
    fraud_count_bal = int(y_train_balanced.sum())
    legit_count_bal = len(y_train_balanced) - fraud_count_bal
    dynamic_spw     = legit_count_bal / max(fraud_count_bal, 1)

    xgb_params = dict(params['xgboost'])    # copy so we don't mutate config
    if xgb_params.get('scale_pos_weight') is None:
        xgb_params['scale_pos_weight'] = dynamic_spw * 0.8   # slight dampening

    print("\n" + "-" * 70)
    print("TRAINING XGBOOST")
    print("-" * 70)
    print(f"  scale_pos_weight  : {xgb_params['scale_pos_weight']:.3f}")
    print(f"  max_depth         : {xgb_params['max_depth']}")
    print(f"  min_child_weight  : {xgb_params['min_child_weight']}")
    print(f"  gamma             : {xgb_params['gamma']}")

    xgb_model = xgb.XGBClassifier(**xgb_params)
    xgb_model.fit(
        X_train_balanced,
        y_train_balanced,
        eval_set=[(X_test_scaled, y_test)],
        verbose=False,
    )

    xgb_proba = xgb_model.predict_proba(X_test_scaled)[:, 1]
    xgb_auc   = roc_auc_score(y_test, xgb_proba)
    print(f"\n  XGBoost ROC-AUC : {xgb_auc:.4f}")

    # ------------------------------------------------------------------
    # 7. Isolation Forest — trained ONLY on legitimate training samples
    # ------------------------------------------------------------------
    print("\n" + "-" * 70)
    print("TRAINING ISOLATION FOREST (legitimate claims only)")
    print("-" * 70)

    # Use the original (pre-SMOTE) scaled training data for the filter
    legit_mask          = (y_train.values == False) | (y_train.values == 0)
    X_train_legit       = X_train_scaled[legit_mask]

    iso_params = params['isolation_forest']
    iso_forest = IsolationForest(**iso_params)
    iso_forest.fit(X_train_legit)

    anomaly_scores_raw = -iso_forest.score_samples(X_test_scaled)
    # Normalise to [0, 1]: higher = more anomalous
    a_min, a_max = anomaly_scores_raw.min(), anomaly_scores_raw.max()
    if a_max > a_min:
        anomaly_norm = (anomaly_scores_raw - a_min) / (a_max - a_min)
    else:
        anomaly_norm = np.zeros_like(anomaly_scores_raw)

    iso_anomaly_count = (iso_forest.predict(X_test_scaled) == -1).sum()
    print(f"  Isolation Forest flagged {iso_anomaly_count} anomalies in test set")

    # ------------------------------------------------------------------
    # 8. Ensemble score — weights from ml_config
    # ------------------------------------------------------------------
    xgb_w = ENSEMBLE_WEIGHTS['xgboost']
    iso_w = ENSEMBLE_WEIGHTS['isolation_forest']

    ensemble_proba = xgb_w * xgb_proba + iso_w * anomaly_norm

    print("\n" + "-" * 70)
    print(f"ENSEMBLE  ({xgb_w*100:.0f}% XGBoost  +  {iso_w*100:.0f}% Isolation Forest)")
    print("-" * 70)

    ensemble_auc = roc_auc_score(y_test, ensemble_proba)
    print(f"  Ensemble ROC-AUC : {ensemble_auc:.4f}")

    # ------------------------------------------------------------------
    # 9. Threshold selection on ensemble scores
    # ------------------------------------------------------------------
    best_threshold, best_f1 = _select_best_threshold(y_test, ensemble_proba)
    print(f"\n  ✓ Best threshold : {best_threshold}  (Fraudulent F1={best_f1:.3f})")

    ensemble_pred = (ensemble_proba >= best_threshold).astype(int)

    print("\nFinal ensemble performance at chosen threshold:")
    print(classification_report(
        y_test, ensemble_pred,
        target_names=['Legitimate', 'Fraudulent'],
        zero_division=0,
    ))

    # ------------------------------------------------------------------
    # 10. Feature importance
    # ------------------------------------------------------------------
    print("\n" + "-" * 70)
    print("TOP FEATURE IMPORTANCES (XGBoost)")
    print("-" * 70)

    fi_df = (
        pd.DataFrame({
            'feature':    available_features,
            'importance': xgb_model.feature_importances_,
        })
        .sort_values('importance', ascending=False)
        .head(15)
    )
    print(fi_df.to_string(index=False))

    # ------------------------------------------------------------------
    # 11. Persist models and artefacts
    # ------------------------------------------------------------------
    print("\n" + "-" * 70)
    print("SAVING MODELS")
    print("-" * 70)

    model_dir = FRAUD_DETECTION_MODEL_PATH.parent
    model_dir.mkdir(parents=True, exist_ok=True)

    joblib.dump(xgb_model,         FRAUD_DETECTION_MODEL_PATH)
    joblib.dump(iso_forest,        FRAUD_ISOLATION_FOREST_PATH)
    joblib.dump(scaler,            FRAUD_SCALER_PATH)
    joblib.dump(available_features, FRAUD_FEATURES_PATH)
    joblib.dump({'optimal_threshold': best_threshold}, FRAUD_THRESHOLD_PATH)

    print(f"  ✓ XGBoost model       → {FRAUD_DETECTION_MODEL_PATH}")
    print(f"  ✓ Isolation Forest    → {FRAUD_ISOLATION_FOREST_PATH}")
    print(f"  ✓ Scaler              → {FRAUD_SCALER_PATH}")
    print(f"  ✓ Feature list        → {FRAUD_FEATURES_PATH}")
    print(f"  ✓ Threshold           → {FRAUD_THRESHOLD_PATH}")

    # ------------------------------------------------------------------
    # 12. Confusion matrix plot
    # ------------------------------------------------------------------
    plt.figure(figsize=(8, 6))
    cm = confusion_matrix(y_test, ensemble_pred)
    sns.heatmap(
        cm, annot=True, fmt='d', cmap='Blues',
        xticklabels=['Legitimate', 'Fraudulent'],
        yticklabels=['Legitimate', 'Fraudulent'],
    )
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.title(f'Confusion Matrix — Ensemble (threshold={best_threshold})')
    plt.tight_layout()
    cm_path = model_dir / 'fraud_confusion_matrix.png'
    plt.savefig(cm_path, dpi=300)
    plt.close()
    print(f"  ✓ Confusion matrix    → {cm_path}")

    # ------------------------------------------------------------------
    # 13. ROC curve plot
    # ------------------------------------------------------------------
    fpr, tpr, _ = roc_curve(y_test, ensemble_proba)
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, label=f'Ensemble (AUC = {ensemble_auc:.3f})')
    plt.plot([0, 1], [0, 1], 'k--', label='Random')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC Curve — Fraud Detection Ensemble')
    plt.legend()
    plt.tight_layout()
    roc_path = model_dir / 'fraud_roc_curve.png'
    plt.savefig(roc_path, dpi=300)
    plt.close()
    print(f"  ✓ ROC curve           → {roc_path}")

    # ------------------------------------------------------------------
    # 14. Summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("FRAUD DETECTION MODEL TRAINING COMPLETE")
    print("=" * 70)
    print(f"\n  Features used      : {len(available_features)}")
    print(f"  SMOTE enabled      : {params.get('use_smote', True)}")
    print(f"  Optimal threshold  : {best_threshold}")
    print(f"  XGBoost AUC        : {xgb_auc:.1%}")
    print(f"  Ensemble AUC       : {ensemble_auc:.1%}")
    print(f"  Ensemble weights   : XGBoost={xgb_w}, IsoForest={iso_w}")
    print(f"  Risk thresholds    : {FRAUD_RISK_THRESHOLDS}")


if __name__ == '__main__':
    train_fraud_detection_model()