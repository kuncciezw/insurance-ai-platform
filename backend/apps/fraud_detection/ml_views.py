"""
API Views for Machine Learning Fraud Detection Pipeline
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd
from django.db.models import Avg, Count, Q
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from system_settings.models import GlobalPricingSettings
from ml_models.feature_engineering import FeatureEngineer
from ml_models.model_loader import get_model_loader
from .models import Claim, Policy, Policyholder, Vehicle
from .serializers import ClaimSerializer

# Singleton ML model instances
model_loader = get_model_loader()
feature_engineer = FeatureEngineer()


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def analyze_claim_fraud(request: Request) -> Response:
    """
    POST /api/fraud-detection/fraud/analyze-claim/

    Option A — existing claim:   { "claim_id": "<uuid>" }
    Option B — synthetic data:   { "policy_age_days": 365, "claimed_amount": 5000, ... }
    """
    try:
        claim_id = request.data.get("claim_id")
        if claim_id:
            return _analyze_existing_claim(str(claim_id))
        return _analyze_new_claim_data(request.data)  # type: ignore[arg-type]
    except Exception as exc:
        import traceback
        traceback.print_exc()
        return Response(
            {"error": f"Error analyzing claim: {exc}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def batch_analyze_claims(request: Request) -> Response:
    """Batch analyze up to 100 claims for fraud using global settings."""
    try:
        claim_ids = request.data.get("claim_ids")
        filter_type = request.data.get("filter", "all_pending")

        if claim_ids:
            claims = Claim.objects.filter(id__in=claim_ids)
        elif filter_type == "all_pending":
            claims = Claim.objects.filter(claim_status__in=["SUBMITTED", "UNDER_REVIEW"])
        elif filter_type == "recent":
            claims = Claim.objects.filter(submitted_date__gte=timezone.now() - timedelta(days=30))
        elif filter_type == "high_value":
            settings = GlobalPricingSettings.get_solo()
            claims = Claim.objects.filter(claimed_amount__gte=settings.threshold_manual_review)
        else:
            return Response({"error": "Invalid filter type"}, status=status.HTTP_400_BAD_REQUEST)

        if claims.count() == 0:
            return Response({"message": "No claims found", "results": []})
        if claims.count() > 100:
            return Response(
                {"error": f"Batch too large ({claims.count()} claims). Maximum 100."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        policies = Policy.objects.filter(id__in=claims.values_list("policy_id", flat=True))
        policyholders = Policyholder.objects.filter(
            id__in=policies.values_list("policyholder_id", flat=True)
        )
        vehicles = Vehicle.objects.filter(id__in=policies.values_list("vehicle_id", flat=True))

        claims_list = list(claims.values())
        for i, c in enumerate(claims_list):
            c["numeric_id"] = i
        claims_df = pd.DataFrame(claims_list)
        claims_df["id"] = claims_df["numeric_id"]

        policyholders_df = pd.DataFrame(list(policyholders.values()))
        vehicles_df = pd.DataFrame(list(vehicles.values()))
        policies_df = pd.DataFrame(list(policies.values()))

        policy_id_map = {str(p["id"]): i for i, p in enumerate(policies_df.to_dict("records"))}
        policyholder_id_map = {str(p["id"]): i for i, p in enumerate(policyholders_df.to_dict("records"))}
        vehicle_id_map = {str(v["id"]): i for i, v in enumerate(vehicles_df.to_dict("records"))}

        claims_df["policy_id"] = claims_df["policy_id"].astype(str).map(policy_id_map).fillna(0).astype(int)
        policies_df["id"] = range(len(policies_df))
        policies_df["policyholder_id"] = policies_df["policyholder_id"].astype(str).map(policyholder_id_map).fillna(0).astype(int)
        policies_df["vehicle_id"] = policies_df["vehicle_id"].astype(str).map(vehicle_id_map).fillna(0).astype(int)
        policyholders_df["id"] = range(len(policyholders_df))
        vehicles_df["id"] = range(len(vehicles_df))

        engineered_df = feature_engineer.engineer_fraud_detection_features(
            claims_df, policyholders_df, vehicles_df, policies_df
        )

        results = []
        risk_counts = {"HIGH": 0, "CRITICAL": 0, "MEDIUM": 0, "LOW": 0}

        for idx, row in engineered_df.iterrows():
            pred = model_loader.predict_fraud(row)
            orig_claim = claims_list[idx]
            risk_level = str(pred["risk_level"])
            risk_counts[risk_level] = risk_counts.get(risk_level, 0) + 1
            results.append({
                "claim_id": str(orig_claim["id"]),
                "claim_number": str(orig_claim["claim_number"]),
                "claimed_amount": float(orig_claim["claimed_amount"]),
                "fraud_probability": round(float(pred["fraud_probability"]), 4),
                "risk_level": risk_level,
                "is_fraudulent": bool(pred["is_fraudulent"]),
            })

        results.sort(key=lambda x: x["fraud_probability"], reverse=True)

        return Response({
            "total_analyzed": len(results),
            "high_risk_count": risk_counts["HIGH"] + risk_counts["CRITICAL"],
            "medium_risk_count": risk_counts["MEDIUM"],
            "low_risk_count": risk_counts["LOW"],
            "risk_breakdown": risk_counts,
            "results": results,
            "analyzed_at": timezone.now().isoformat(),
        })

    except Exception as exc:
        import traceback
        traceback.print_exc()
        return Response(
            {"error": f"Batch analysis error: {exc}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_high_risk_claims(request: Request) -> Response:
    """Return claims whose stored fraud_score exceeds a threshold."""
    try:
        settings = GlobalPricingSettings.get_solo()
        default_threshold = float(settings.threshold_variance_warning)

        threshold = float(request.GET.get("threshold", default_threshold))
        limit = min(int(request.GET.get("limit", 20)), 100)

        claims = Claim.objects.filter(
            fraud_score__gte=threshold
        ).select_related("policy", "policy__policyholder", "policy__vehicle")[:limit]

        results = [{
            "claim_id": str(c.id),
            "claim_number": str(c.claim_number),
            "claimed_amount": float(c.claimed_amount),
            "claim_type": str(c.claim_type),
            "severity": str(c.severity),
            "fraud_probability": round(float(c.fraud_score or 0), 4),
            "submitted_date": c.submitted_date.isoformat(),
            "policyholder_name": f"{c.policy.policyholder.first_name} {c.policy.policyholder.last_name}",
        } for c in claims]

        return Response({"count": len(results), "threshold": threshold, "results": results})

    except Exception as exc:
        return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def fraud_statistics(request: Request) -> Response:
    """Aggregate fraud statistics across all claims."""
    try:
        settings = GlobalPricingSettings.get_solo()
        total_claims = Claim.objects.count()
        fraudulent_claims = Claim.objects.filter(is_fraudulent=True).count()
        high_fraud_score = Claim.objects.filter(fraud_score__gte=settings.threshold_fraud_reject).count()
        fraud_rate = fraudulent_claims / total_claims if total_claims > 0 else 0
        avg_fraud_score = Claim.objects.aggregate(Avg("fraud_score"))["fraud_score__avg"] or 0

        by_claim_type = {}
        for ct in ["ACCIDENT", "THEFT", "VANDALISM", "NATURAL_DISASTER", "FIRE", "OTHER"]:
            total = Claim.objects.filter(claim_type=ct).count()
            count = Claim.objects.filter(claim_type=ct, is_fraudulent=True).count()
            by_claim_type[ct] = {
                "fraudulent": count, "total": total,
                "fraud_rate": count / total if total > 0 else 0,
            }

        by_severity = {}
        for sv in ["MINOR", "MODERATE", "MAJOR", "TOTAL_LOSS"]:
            total = Claim.objects.filter(severity=sv).count()
            count = Claim.objects.filter(severity=sv, is_fraudulent=True).count()
            by_severity[sv] = {
                "fraudulent": count, "total": total,
                "fraud_rate": count / total if total > 0 else 0,
            }

        return Response({
            "total_claims": total_claims,
            "fraudulent_claims": fraudulent_claims,
            "high_risk_claims": high_fraud_score,
            "fraud_rate": round(fraud_rate, 4),
            "average_fraud_score": round(avg_fraud_score, 4),
            "by_claim_type": by_claim_type,
            "by_severity": by_severity,
            "generated_at": timezone.now().isoformat(),
        })

    except Exception as exc:
        return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _analyze_existing_claim(claim_id: str) -> Response:
    try:
        claim = Claim.objects.get(id=claim_id)
    except Claim.DoesNotExist:
        return Response(
            {"error": f"Claim {claim_id} not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    try:
        # ── FIX: import document analyser functions (was missing entirely) ──
        from .document_analyzer import (
            extract_document_text,
            analyze_document_legitimacy,
            compute_combined_fraud_score,
        )

        policy = claim.policy
        policyholder = policy.policyholder
        vehicle = policy.vehicle
        settings = GlobalPricingSettings.get_solo()

        # ── Build feature DataFrames ──────────────────────────────────────
        claims_df = pd.DataFrame([{
            "id": 0, "policy_id": 0,
            "policyholder_id": 0, "vehicle_id": 0,
            "claim_type": str(claim.claim_type),
            "severity": str(claim.severity),
            "claimed_amount": float(claim.claimed_amount),
            "incident_date": claim.incident_date,
            "submitted_date": claim.submitted_date,
            "number_of_vehicles_involved": int(claim.number_of_vehicles_involved or 1),
        }])

        policyholders_df = pd.DataFrame([{
            "id": 0,
            "policy_holder_id": str(policyholder.policy_holder_id),
            "date_of_birth": policyholder.date_of_birth,
            "credit_score": int(policyholder.credit_score or 650),
            "years_with_company": float(policyholder.years_with_company or 0),
            "is_medical_license_valid": bool(policyholder.is_medical_license_valid),
            "has_defensive_license": bool(policyholder.has_defensive_license),
        }])

        vehicles_df = pd.DataFrame([{
            "id": 0,
            "manufacture_year": int(vehicle.manufacture_year),
            "market_value": float(vehicle.market_value),
            "has_anti_theft": bool(vehicle.has_anti_theft),
            "is_modified": bool(vehicle.is_modified),
        }])

        policies_df = pd.DataFrame([{
            "id": 0, "policyholder_id": 0, "vehicle_id": 0,
            "start_date": policy.start_date,
            "coverage_amount": float(policy.coverage_amount),
        }])

        # ── Feature engineering ───────────────────────────────────────────
        engineered_df = feature_engineer.engineer_fraud_detection_features(
            claims_df, policyholders_df, vehicles_df, policies_df
        )

        # ── ML prediction ─────────────────────────────────────────────────
        prediction = model_loader.predict_fraud(engineered_df.iloc[0])
        ml_fraud_score = float(prediction["fraud_probability"])

        # ── SHAP explanation ──────────────────────────────────────────────
        try:
            shap_explanation = model_loader.explain_fraud_prediction(engineered_df)
        except Exception as exc:
            shap_explanation = {
                "error": str(exc),
                "risk_increasers": [], "risk_decreasers": [], "top_features": [],
            }

        # ── FIX: document analysis (was entirely absent) ──────────────────
        # Mirrors the same logic used in signals.py _run_pipeline so both
        # paths produce the same combined score.
        if claim.incident_evidence:
            doc_text = extract_document_text(claim.incident_evidence)
            if doc_text:
                doc_legitimacy, doc_flags = analyze_document_legitimacy(doc_text, claim)
            else:
                # File exists but could not be read
                doc_legitimacy = 0.40
                doc_flags = ["Evidence file present but could not be read."]
        else:
            # No evidence uploaded — treat as a risk signal
            doc_legitimacy = 0.35
            doc_flags = ["No supporting evidence document uploaded."]

        # ── FIX: combined score (was using raw ml_fraud_score only) ───────
        # ML model carries 65% weight; document legitimacy carries 35%.
        # (1 - doc_legitimacy) converts the legitimacy score into a fraud
        # direction so both components pull in the same direction.
        combined_score = compute_combined_fraud_score(ml_fraud_score, doc_legitimacy)

        risk_factors = _get_risk_factors(claim, policy, policyholder)
        recommendation, automated_action, explanation = _get_recommendation(combined_score, settings)

        # ── FIX: persist combined score, not raw ML score ─────────────────
        # Previously saved fraud_prob (ML only) which overwrote the correct
        # combined score that signals.py had already stored on claim creation.
        claim.fraud_score = combined_score
        claim.is_fraudulent = combined_score >= float(settings.threshold_fraud_reject)
        claim.save(update_fields=["fraud_score", "is_fraudulent"])

        return Response({
            "claim_id": str(claim.id),
            "claim_number": str(claim.claim_number),
            "claimed_amount": float(claim.claimed_amount),
            "fraud_score": round(combined_score, 4),
            "is_fraudulent": claim.is_fraudulent,
            "fraud_analysis": {
                # ── FIX: expose combined score as the headline probability ─
                "fraud_probability": round(combined_score, 4),
                "is_fraudulent": claim.is_fraudulent,
                "risk_level": str(prediction["risk_level"]),
                "confidence": prediction["confidence"],
                "xgboost_probability": round(float(prediction.get("xgboost_probability", ml_fraud_score)), 4),
                "anomaly_score": round(float(prediction.get("anomaly_score", 0)), 4),
                "threshold_used": round(float(settings.threshold_fraud_reject), 4),
                # ── FIX: new fields so frontend can show document breakdown ─
                "ml_score": round(ml_fraud_score, 4),
                "document_legitimacy": round(doc_legitimacy, 4),
                "document_flags": doc_flags,
            },
            "model_explanation": shap_explanation,
            "risk_factors": risk_factors or ["No significant risk factors detected"],
            "recommendation": str(recommendation),
            "automated_action": str(automated_action),
            "explanation": str(explanation),
            "analyzed_at": timezone.now().isoformat(),
        }, status=status.HTTP_200_OK)

    except Exception as exc:
        import traceback
        traceback.print_exc()
        return Response(
            {"error": f"Error analyzing claim: {exc}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def _analyze_new_claim_data(data: dict[str, Any]) -> Response:
    required = [
        "policy_age_days", "claim_delay_days", "claimed_amount",
        "policy_premium", "vehicle_age_years", "driver_age",
    ]
    missing = [f for f in required if f not in data]
    if missing:
        return Response(
            {"error": f"Missing required fields: {', '.join(missing)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        severity_map = {
            "Minor Damage": "MINOR", "Trivial Damage": "MINOR",
            "Major Damage": "MAJOR", "Total Loss": "TOTAL_LOSS",
        }
        type_map = {
            "Collision": "ACCIDENT", "Theft": "THEFT",
            "Fire": "FIRE", "Vandalism": "VANDALISM",
            "Natural Disaster": "NATURAL_DISASTER",
            "Other": "OTHER",
        }

        today = datetime.now()
        incident_date = today - timedelta(days=int(data.get("claim_delay_days", 0)))
        policy_start = today - timedelta(days=int(data.get("policy_age_days", 365)))
        settings = GlobalPricingSettings.get_solo()

        claims_df = pd.DataFrame([{
            "id": 0, "policy_id": 0, "policyholder_id": 0, "vehicle_id": 0,
            "claim_type": type_map.get(data.get("incident_type", "Collision"), "ACCIDENT"),
            "severity": severity_map.get(data.get("incident_severity", "Major Damage"), "MAJOR"),
            "claimed_amount": float(data["claimed_amount"]),
            "incident_date": incident_date,
            "submitted_date": today,
            "number_of_vehicles_involved": 2,
        }])

        birth_year = today.year - int(data.get("driver_age", 35))
        policyholders_df = pd.DataFrame([{
            "id": 0,
            "policy_holder_id": "SYNTH000",
            "date_of_birth": datetime(birth_year, 1, 1).date(),
            "credit_score": 650,
            "years_with_company": float(data.get("policy_age_days", 365)) / 365,
            "is_medical_license_valid": True,
            "has_defensive_license": False,
        }])

        vehicle_year = today.year - int(data.get("vehicle_age_years", 5))
        vehicles_df = pd.DataFrame([{
            "id": 0,
            "manufacture_year": vehicle_year,
            "market_value": float(data.get("claimed_amount", 5000)) * 1.5,
            "has_anti_theft": False,
            "is_modified": False,
        }])

        estimated_coverage = float(data["policy_premium"]) * 10
        policies_df = pd.DataFrame([{
            "id": 0, "policyholder_id": 0, "vehicle_id": 0,
            "start_date": policy_start.date(),
            "coverage_amount": max(estimated_coverage, float(data["claimed_amount"]) * 1.2),
        }])

        engineered_df = feature_engineer.engineer_fraud_detection_features(
            claims_df, policyholders_df, vehicles_df, policies_df
        )
        prediction = model_loader.predict_fraud(engineered_df.iloc[0])
        fraud_prob = float(prediction["fraud_probability"])

        try:
            shap_explanation = model_loader.explain_fraud_prediction(engineered_df)
        except Exception as exc:
            shap_explanation = {
                "error": str(exc),
                "risk_increasers": [], "risk_decreasers": [], "top_features": [],
            }

        # Synthetic claims have no uploaded evidence — note this clearly
        # so callers understand the score is ML-only for synthetic data.
        risk_factors = []
        if int(data.get("policy_age_days", 365)) < 30:
            risk_factors.append("Very new policy (< 30 days)")
        if int(data.get("claim_delay_days", 0)) > 7:
            risk_factors.append(f"Late submission ({data['claim_delay_days']} days after incident)")
        ratio = float(data["claimed_amount"]) / float(data["policy_premium"])
        if ratio > 5:
            risk_factors.append(f"High claim-to-premium ratio ({ratio:.1f}×)")
        if int(data.get("previous_claims", 0)) >= 3:
            risk_factors.append(f"Multiple prior claims ({data['previous_claims']})")
        hour = int(data.get("incident_hour", 14))
        if hour >= 23 or hour <= 4:
            risk_factors.append(f"High-risk incident hour ({hour}:00)")
        if int(data.get("vehicle_age_years", 0)) > 10 and float(data["claimed_amount"]) > 10000:
            risk_factors.append("High claim amount for an older vehicle")

        recommendation, automated_action, explanation = _get_recommendation(fraud_prob, settings)
        is_fraud = fraud_prob >= float(settings.threshold_fraud_reject)

        return Response({
            "fraud_score": round(fraud_prob, 4),
            "is_fraudulent": is_fraud,
            "fraud_analysis": {
                "fraud_probability": round(fraud_prob, 4),
                "is_fraudulent": is_fraud,
                "risk_level": str(prediction["risk_level"]),
                "confidence": prediction["confidence"],
                "xgboost_probability": round(float(prediction.get("xgboost_probability", fraud_prob)), 4),
                "anomaly_score": round(float(prediction.get("anomaly_score", 0)), 4),
                # Synthetic data — no document to analyse
                "ml_score": round(fraud_prob, 4),
                "document_legitimacy": None,
                "document_flags": ["No evidence document — synthetic claim data"],
            },
            "model_explanation": shap_explanation,
            "risk_factors": risk_factors or ["No significant risk factors detected"],
            "recommendation": str(recommendation),
            "automated_action": str(automated_action),
            "explanation": str(explanation),
            "analyzed_at": timezone.now().isoformat(),
            "claim_details": {
                "claimed_amount": float(data["claimed_amount"]),
                "incident_type": str(data.get("incident_type")),
                "severity": str(data.get("incident_severity")),
                "policy_age_days": int(data.get("policy_age_days")),
            },
        }, status=status.HTTP_200_OK)

    except Exception as exc:
        import traceback
        traceback.print_exc()
        return Response(
            {"error": f"Error analyzing claim: {exc}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def _get_risk_factors(claim: Claim, policy: Policy, policyholder: Policyholder) -> list[str]:
    risk_factors = []
    try:
        if float(claim.claimed_amount or 0) / max(float(policy.coverage_amount or 1), 1) > 0.8:
            risk_factors.append("High claim amount relative to policy coverage")
        if claim.incident_date and policy.start_date:
            days_since_start = (claim.incident_date.date() - policy.start_date).days
            if days_since_start < 30:
                risk_factors.append("Claim filed shortly after policy inception")
        if claim.submitted_date and claim.incident_date:
            delay_h = (claim.submitted_date - claim.incident_date).total_seconds() / 3600
            if delay_h > 72:
                risk_factors.append("Delayed submission (> 72 hours after incident)")
        if not policyholder.is_medical_license_valid:
            risk_factors.append("Invalid medical licence at time of claim")
        if not policyholder.has_driving_license:
            risk_factors.append("No valid driving licence on file")
        total_claims = Claim.objects.filter(policy__policyholder=policyholder).count()
        if total_claims >= 3:
            risk_factors.append(f"Multiple claims history ({total_claims} total)")
        if policyholder.credit_score and policyholder.credit_score < 600:
            risk_factors.append(f"Low credit score ({policyholder.credit_score})")
    except Exception as exc:
        print(f"Risk factor extraction error: {exc}")
    return risk_factors


def _get_recommendation(fraud_prob: float, settings: GlobalPricingSettings) -> tuple[str, str, str]:
    """
    Evaluates combined fraud probability against Singleton configuration thresholds.
    Note: fraud_prob here is always the combined score (ML + document), never raw ML only.
    """
    reject_threshold = float(settings.threshold_fraud_reject)
    warning_threshold = float(settings.threshold_variance_warning)

    if fraud_prob >= reject_threshold:
        return (
            "REJECT_CLAIM", "REJECT",
            f"Strong fraud indicators. Exceeds global system rejection threshold ({reject_threshold:.2%}).",
        )
    if fraud_prob >= warning_threshold:
        return (
            "DETAILED_INVESTIGATION", "HOLD",
            f"Elevated risk. Exceeds variance review warning threshold ({warning_threshold:.2%}). Claim held for investigation.",
        )
    if fraud_prob >= 0.35:
        return (
            "MANUAL_REVIEW", "HOLD",
            "Moderate risk profile. Routine human audit recommended before processing.",
        )
    return (
        "APPROVE_PROCESSING", "PROCEED",
        "Low fraud risk. Claim cleared for standard automated settlement tracks.",
    )