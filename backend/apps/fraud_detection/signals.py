"""
apps/fraud_detection/signals.py

Post-save signal — automatically processes every newly created Claim.

Pipeline (runs once per new Claim, skipped on updates)
───────────────────────────────────────────────────────
1. Build feature DataFrames from the Claim's related objects
2. Run the ML ensemble → fraud score
3. Run SHAP → human-readable explanation
4. Extract & score the evidence document
5. Compute a combined score (ML 65% + document 35%)
6. Auto-approve (≤0.50) or auto-reject (>0.50)
7. Persist via .update() — avoids re-triggering the signal
"""

import logging
import pandas as pd
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Claim

logger = logging.getLogger(__name__)

# ── Auto-reject threshold (must match _get_recommendation in ml_views.py)
AUTO_REJECT_THRESHOLD = 0.50


@receiver(post_save, sender=Claim)
def auto_process_new_claim(sender, instance, created, **kwargs):
    """Fires once per new Claim only; ignored on updates."""
    if not created:
        return

    logger.info("Auto-processing new claim %s ...", instance.claim_number)
    try:
        _run_pipeline(instance)
    except Exception:
        logger.exception(
            "Auto-processing pipeline failed for claim %s", instance.claim_number
        )


# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE
# ─────────────────────────────────────────────────────────────────────────────

def _run_pipeline(claim: Claim) -> None:
    from ml_models.model_loader import get_model_loader
    from ml_models.feature_engineering import FeatureEngineer
    from .document_analyzer import (
        extract_document_text,
        analyze_document_legitimacy,
        compute_combined_fraud_score,
    )

    model_loader     = get_model_loader()
    feature_engineer = FeatureEngineer()

    policy       = claim.policy
    policyholder = policy.policyholder
    vehicle      = policy.vehicle

    # ── Step 1: build DataFrames with integer IDs (avoids UUID mapping) ───
    # All IDs are set to 0 — foreign key merges resolve correctly for a
    # single row because every join partner also has id=0.
    claims_df = pd.DataFrame([{
        "id":              0,
        "policy_id":       0,
        "policyholder_id": 0,
        "vehicle_id":      0,
        "claim_type":               str(claim.claim_type),
        "severity":                 str(claim.severity),
        "claimed_amount":           float(claim.claimed_amount),
        "incident_date":            claim.incident_date,
        "submitted_date":           claim.submitted_date,
        "number_of_vehicles_involved": int(claim.number_of_vehicles_involved or 1),
    }])

    policyholders_df = pd.DataFrame([{
        "id":                     0,
        "policy_holder_id":       str(policyholder.policy_holder_id),
        "date_of_birth":          policyholder.date_of_birth,
        "credit_score":           int(policyholder.credit_score or 650),
        "years_with_company":     float(policyholder.years_with_company or 0),
        "is_medical_license_valid": bool(policyholder.is_medical_license_valid),
        "has_defensive_license":  bool(policyholder.has_defensive_license),
    }])

    vehicles_df = pd.DataFrame([{
        "id":             0,
        "manufacture_year": int(vehicle.manufacture_year),
        "market_value":   float(vehicle.market_value),
        "has_anti_theft": bool(vehicle.has_anti_theft),
        "is_modified":    bool(vehicle.is_modified),
    }])

    # policies_df must include policyholder_id and vehicle_id so the
    # feature engineer's UUID-mapping branch can find them if needed.
    policies_df = pd.DataFrame([{
        "id":              0,
        "policyholder_id": 0,
        "vehicle_id":      0,
        "start_date":      policy.start_date,
        "coverage_amount": float(policy.coverage_amount),
    }])

    # ── Step 2: engineer features ─────────────────────────────────────────
    engineered_df = feature_engineer.engineer_fraud_detection_features(
        claims_df, policyholders_df, vehicles_df, policies_df
    )

    # ── Step 3: ML fraud prediction ───────────────────────────────────────
    prediction     = model_loader.predict_fraud(engineered_df.iloc[0])
    ml_fraud_score = float(prediction["fraud_probability"])

    # ── Step 4: SHAP explanation ──────────────────────────────────────────
    shap_explanation: dict = {}
    try:
        shap_explanation = model_loader.explain_fraud_prediction(engineered_df)
    except Exception as exc:
        logger.warning("SHAP explanation skipped for %s: %s", claim.claim_number, exc)

    # ── Step 5: evidence document analysis ───────────────────────────────
    if instance.incident_evidence:
        doc_text = extract_document_text(instance.incident_evidence)
        if doc_text:
            doc_legitimacy, doc_flags = analyze_document_legitimacy(doc_text, claim)
        else:
            # File exists but could not be read
            doc_legitimacy = 0.40
            doc_flags      = ["Evidence file present but could not be read."]
    else:
        # No evidence uploaded — treat as a risk signal
        doc_legitimacy = 0.35
        doc_flags      = ["No supporting evidence document uploaded."]

    logger.debug(
        "Claim %s — ML=%.3f  doc_legitimacy=%.3f  flags=%s",
        claim.claim_number, ml_fraud_score, doc_legitimacy, doc_flags,
    )

    # ── Step 6: combined score ────────────────────────────────────────────
    combined_score = compute_combined_fraud_score(ml_fraud_score, doc_legitimacy)

    # ── Step 7: auto decision ─────────────────────────────────────────────
    is_fraudulent = combined_score > AUTO_REJECT_THRESHOLD

    if not is_fraudulent:
        new_status   = "APPROVED"
        approved_amt = float(claim.claimed_amount)
        fraud_reason = None
    else:
        new_status   = "REJECTED"
        approved_amt = 0.0
        fraud_reason = _build_rejection_reason(
            combined_score, ml_fraud_score, doc_legitimacy,
            doc_flags, shap_explanation,
        )

    # ── Step 8: persist — .update() avoids re-triggering the signal ──────
    Claim.objects.filter(id=claim.id).update(
        fraud_score     = combined_score,
        is_fraudulent   = is_fraudulent,
        claim_status    = new_status,
        approved_amount = approved_amt,
        fraud_reason    = fraud_reason,
        reviewed_date   = timezone.now(),
    )

    logger.info(
        "Claim %s processed — combined=%.3f  ML=%.3f  doc=%.3f → %s",
        claim.claim_number, combined_score, ml_fraud_score, doc_legitimacy, new_status,
    )


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _build_rejection_reason(
    combined:         float,
    ml_score:         float,
    doc_legitimacy:   float,
    doc_flags:        list,
    shap_explanation: dict,
) -> str:
    """Compose a concise, human-readable rejection reason for the adjuster."""
    parts = [
        f"Auto-rejected: combined fraud score {combined:.1%}.",
        f"ML model score: {ml_score:.1%}.",
        f"Document legitimacy: {doc_legitimacy:.1%}.",
    ]

    if doc_flags:
        parts.append("Document issues: " + "; ".join(doc_flags[:3]) + ".")

    top_risk = shap_explanation.get("risk_increasers", [])[:3]
    if top_risk:
        labels = [f["label"] for f in top_risk]
        parts.append("Top ML risk factors: " + ", ".join(labels) + ".")

    return " ".join(parts)