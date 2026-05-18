from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta, datetime
import pandas as pd
import numpy as np
 
from .models import Claim, Policy, Policyholder, Vehicle
from .serializers import ClaimSerializer
from ml_models.model_loader import get_model_loader
from ml_models.feature_engineering import FeatureEngineer
 
 
# Singleton instances
model_loader     = get_model_loader()
feature_engineer = FeatureEngineer()
 
 
# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC ENDPOINT
# ═══════════════════════════════════════════════════════════════════════════════
 
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def analyze_claim_fraud(request):
    """
    POST /api/fraud-detection/fraud/analyze-claim/
 
    Option A — existing claim:   { "claim_id": "<uuid>" }
    Option B — synthetic data:   { "policy_age_days": 365, "claimed_amount": 5000, ... }
    """
    try:
        claim_id = request.data.get("claim_id")
        if claim_id:
            return _analyze_existing_claim(claim_id)
        return _analyze_new_claim_data(request.data)
    except Exception as exc:
        import traceback
        traceback.print_exc()
        return Response(
            {"error": f"Error analyzing claim: {exc}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
 
 
# ═══════════════════════════════════════════════════════════════════════════════
# PRIVATE HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
 
def _analyze_existing_claim(claim_id: str) -> Response:
    try:
        claim = Claim.objects.get(id=claim_id)
    except Claim.DoesNotExist:
        return Response(
            {"error": f"Claim {claim_id} not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
 
    try:
        policy       = claim.policy
        policyholder = policy.policyholder
        vehicle      = policy.vehicle
 
        # ── build feature DataFrames (integer IDs — no UUID mapping needed)
        claims_df = pd.DataFrame([{
            "id":              0, "policy_id": 0,
            "policyholder_id": 0, "vehicle_id": 0,
            "claim_type":               str(claim.claim_type),
            "severity":                 str(claim.severity),
            "claimed_amount":           float(claim.claimed_amount),
            "incident_date":            claim.incident_date,
            "submitted_date":           claim.submitted_date,
            "number_of_vehicles_involved": int(claim.number_of_vehicles_involved or 1),
        }])
 
        policyholders_df = pd.DataFrame([{
            "id": 0,
            "policy_holder_id":        str(policyholder.policy_holder_id),
            "date_of_birth":           policyholder.date_of_birth,
            "credit_score":            int(policyholder.credit_score or 650),
            "years_with_company":      float(policyholder.years_with_company or 0),
            "is_medical_license_valid":bool(policyholder.is_medical_license_valid),
            "has_defensive_license":   bool(policyholder.has_defensive_license),
        }])
 
        vehicles_df = pd.DataFrame([{
            "id": 0,
            "manufacture_year": int(vehicle.manufacture_year),
            "market_value":     float(vehicle.market_value),
            "has_anti_theft":   bool(vehicle.has_anti_theft),
            "is_modified":      bool(vehicle.is_modified),
        }])
 
        policies_df = pd.DataFrame([{
            "id": 0, "policyholder_id": 0, "vehicle_id": 0,
            "start_date":      policy.start_date,
            "coverage_amount": float(policy.coverage_amount),
        }])
 
        # ── feature engineering ───────────────────────────────────────────
        engineered_df = feature_engineer.engineer_fraud_detection_features(
            claims_df, policyholders_df, vehicles_df, policies_df
        )
 
        # ── ML prediction ─────────────────────────────────────────────────
        prediction = model_loader.predict_fraud(engineered_df.iloc[0])
        fraud_prob = float(prediction["fraud_probability"])
 
        # ── SHAP explanation ──────────────────────────────────────────────
        try:
            shap_explanation = model_loader.explain_fraud_prediction(engineered_df)
        except Exception as exc:
            shap_explanation = {
                "error": str(exc),
                "risk_increasers": [], "risk_decreasers": [], "top_features": [],
            }
 
        risk_factors = _get_risk_factors(claim, policy, policyholder)
        recommendation, automated_action, explanation = _get_recommendation(fraud_prob)
 
        # ── persist updated scores ────────────────────────────────────────
        claim.fraud_score   = fraud_prob
        claim.is_fraudulent = fraud_prob >= 0.50
        claim.save(update_fields=["fraud_score", "is_fraudulent"])
 
        return Response({
            "claim_id":       str(claim.id),
            "claim_number":   str(claim.claim_number),
            "claimed_amount": float(claim.claimed_amount),
            "fraud_score":    round(fraud_prob, 4),
            "is_fraudulent":  bool(prediction["is_fraudulent"]),
            "fraud_analysis": {
                "fraud_probability":   round(fraud_prob, 4),
                "is_fraudulent":       bool(prediction["is_fraudulent"]),
                "risk_level":          str(prediction["risk_level"]),
                "confidence":          prediction["confidence"],
                "xgboost_probability": round(float(prediction.get("xgboost_probability", fraud_prob)), 4),
                "anomaly_score":       round(float(prediction.get("anomaly_score", 0)), 4),
                "threshold_used":      round(float(prediction.get("threshold_used", 0.5)), 4),
            },
            "model_explanation": shap_explanation,   # ← NEW
            "risk_factors":   risk_factors or ["No significant risk factors detected"],
            "recommendation": str(recommendation),
            "automated_action": str(automated_action),
            "explanation":    str(explanation),
            "analyzed_at":    timezone.now().isoformat(),
        }, status=status.HTTP_200_OK)
 
    except Exception as exc:
        import traceback
        traceback.print_exc()
        return Response(
            {"error": f"Error analyzing claim: {exc}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
 
 
def _analyze_new_claim_data(data: dict) -> Response:
    required = [
        "policy_age_days", "claim_delay_days", "claimed_amount",
        "policy_premium",  "vehicle_age_years", "driver_age",
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
            "Major Damage": "MAJOR", "Total Loss":     "TOTAL_LOSS",
        }
        type_map = {
            "Collision": "ACCIDENT", "Theft":           "THEFT",
            "Fire":      "FIRE",     "Vandalism":        "VANDALISM",
            "Natural Disaster": "NATURAL_DISASTER",
            "Other":     "OTHER",
        }
 
        today         = datetime.now()
        incident_date = today - timedelta(days=int(data.get("claim_delay_days", 0)))
        policy_start  = today - timedelta(days=int(data.get("policy_age_days", 365)))
 
        claims_df = pd.DataFrame([{
            "id": 0, "policy_id": 0, "policyholder_id": 0, "vehicle_id": 0,
            "claim_type":    type_map.get(data.get("incident_type", "Collision"), "ACCIDENT"),
            "severity":      severity_map.get(data.get("incident_severity", "Major Damage"), "MAJOR"),
            "claimed_amount": float(data["claimed_amount"]),
            "incident_date":  incident_date,
            "submitted_date": today,
            "number_of_vehicles_involved": 2,
        }])
 
        birth_year = today.year - int(data.get("driver_age", 35))
        policyholders_df = pd.DataFrame([{
            "id": 0,
            "policy_holder_id":       "SYNTH000",
            "date_of_birth":          datetime(birth_year, 1, 1).date(),
            "credit_score":           650,
            "years_with_company":     float(data.get("policy_age_days", 365)) / 365,
            "is_medical_license_valid": True,
            "has_defensive_license":  False,
        }])
 
        vehicle_year = today.year - int(data.get("vehicle_age_years", 5))
        vehicles_df = pd.DataFrame([{
            "id": 0,
            "manufacture_year": vehicle_year,
            "market_value":     float(data.get("claimed_amount", 5000)) * 1.5,
            "has_anti_theft":   False,
            "is_modified":      False,
        }])
 
        estimated_coverage = float(data["policy_premium"]) * 10
        policies_df = pd.DataFrame([{
            "id": 0, "policyholder_id": 0, "vehicle_id": 0,
            "start_date":      policy_start.date(),
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
 
        # heuristic risk factors for synthetic data
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
 
        recommendation, automated_action, explanation = _get_recommendation(fraud_prob)
 
        return Response({
            "fraud_score":    round(fraud_prob, 4),
            "is_fraudulent":  bool(prediction["is_fraudulent"]),
            "fraud_analysis": {
                "fraud_probability":   round(fraud_prob, 4),
                "is_fraudulent":       bool(prediction["is_fraudulent"]),
                "risk_level":          str(prediction["risk_level"]),
                "confidence":          prediction["confidence"],
                "xgboost_probability": round(float(prediction.get("xgboost_probability", fraud_prob)), 4),
                "anomaly_score":       round(float(prediction.get("anomaly_score", 0)), 4),
            },
            "model_explanation": shap_explanation,   # ← NEW
            "risk_factors":   risk_factors or ["No significant risk factors detected"],
            "recommendation": str(recommendation),
            "automated_action": str(automated_action),
            "explanation":    str(explanation),
            "analyzed_at":    timezone.now().isoformat(),
            "claim_details":  {
                "claimed_amount": float(data["claimed_amount"]),
                "incident_type":  str(data.get("incident_type")),
                "severity":       str(data.get("incident_severity")),
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
 
 
def _get_risk_factors(claim, policy, policyholder):
    risk_factors = []
    try:
        if float(claim.claimed_amount) / float(policy.coverage_amount) > 0.8:
            risk_factors.append("High claim amount relative to policy coverage")
        days_since_start = (claim.incident_date.date() - policy.start_date).days
        if days_since_start < 30:
            risk_factors.append("Claim filed shortly after policy inception")
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
 
 
def _get_recommendation(fraud_prob: float):
    """
    50 % threshold — identical to AUTO_REJECT_THRESHOLD in signals.py.
    Keep these in sync if you change the threshold.
    """
    if fraud_prob >= 0.80:
        return (
            "REJECT_CLAIM", "REJECT",
            "Strong fraud indicators. Claim auto-rejected.",
        )
    if fraud_prob >= 0.50:
        return (
            "DETAILED_INVESTIGATION", "HOLD",
            "Elevated risk. Claim held for detailed investigation.",
        )
    if fraud_prob >= 0.35:
        return (
            "MANUAL_REVIEW", "HOLD",
            "Moderate risk. Manual review recommended before processing.",
        )
    return (
        "APPROVE_PROCESSING", "PROCEED",
        "Low fraud risk. Claim approved for normal processing.",
    )
 
 
# ═══════════════════════════════════════════════════════════════════════════════
# BATCH ANALYSIS  (unchanged from original)
# ═══════════════════════════════════════════════════════════════════════════════
 
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def batch_analyze_claims(request):
    """Batch analyze up to 100 claims for fraud."""
    try:
        claim_ids   = request.data.get("claim_ids")
        filter_type = request.data.get("filter", "all_pending")
 
        if claim_ids:
            claims = Claim.objects.filter(id__in=claim_ids)
        elif filter_type == "all_pending":
            claims = Claim.objects.filter(claim_status__in=["SUBMITTED", "UNDER_REVIEW"])
        elif filter_type == "recent":
            claims = Claim.objects.filter(submitted_date__gte=timezone.now() - timedelta(days=30))
        elif filter_type == "high_value":
            claims = Claim.objects.filter(claimed_amount__gte=10000)
        else:
            return Response({"error": "Invalid filter type"}, status=status.HTTP_400_BAD_REQUEST)
 
        if claims.count() == 0:
            return Response({"message": "No claims found", "results": []})
        if claims.count() > 100:
            return Response(
                {"error": f"Batch too large ({claims.count()} claims). Maximum 100."},
                status=status.HTTP_400_BAD_REQUEST,
            )
 
        policies     = Policy.objects.filter(id__in=claims.values_list("policy_id", flat=True))
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
        vehicles_df      = pd.DataFrame(list(vehicles.values()))
        policies_df      = pd.DataFrame(list(policies.values()))
 
        policy_id_map      = {str(p["id"]): i for i, p in enumerate(policies_df.to_dict("records"))}
        policyholder_id_map = {str(p["id"]): i for i, p in enumerate(policyholders_df.to_dict("records"))}
        vehicle_id_map     = {str(v["id"]): i for i, v in enumerate(vehicles_df.to_dict("records"))}
 
        claims_df["policy_id"]       = claims_df["policy_id"].astype(str).map(policy_id_map).fillna(0).astype(int)
        policies_df["id"]            = range(len(policies_df))
        policies_df["policyholder_id"] = policies_df["policyholder_id"].astype(str).map(policyholder_id_map).fillna(0).astype(int)
        policies_df["vehicle_id"]    = policies_df["vehicle_id"].astype(str).map(vehicle_id_map).fillna(0).astype(int)
        policyholders_df["id"]       = range(len(policyholders_df))
        vehicles_df["id"]            = range(len(vehicles_df))
 
        engineered_df = feature_engineer.engineer_fraud_detection_features(
            claims_df, policyholders_df, vehicles_df, policies_df
        )
 
        results = []
        risk_counts = {"HIGH": 0, "CRITICAL": 0, "MEDIUM": 0, "LOW": 0}
 
        for idx, row in engineered_df.iterrows():
            pred       = model_loader.predict_fraud(row)
            orig_claim = claims_list[idx]
            risk_level = str(pred["risk_level"])
            risk_counts[risk_level] = risk_counts.get(risk_level, 0) + 1
            results.append({
                "claim_id":          str(orig_claim["id"]),
                "claim_number":      str(orig_claim["claim_number"]),
                "claimed_amount":    float(orig_claim["claimed_amount"]),
                "fraud_probability": round(float(pred["fraud_probability"]), 4),
                "risk_level":        risk_level,
                "is_fraudulent":     bool(pred["is_fraudulent"]),
            })
 
        results.sort(key=lambda x: x["fraud_probability"], reverse=True)
 
        return Response({
            "total_analyzed":   len(results),
            "high_risk_count":  risk_counts["HIGH"] + risk_counts["CRITICAL"],
            "medium_risk_count": risk_counts["MEDIUM"],
            "low_risk_count":   risk_counts["LOW"],
            "risk_breakdown":   risk_counts,
            "results":          results,
            "analyzed_at":      timezone.now().isoformat(),
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
def get_high_risk_claims(request):
    """Return claims whose stored fraud_score exceeds a threshold."""
    try:
        threshold = float(request.GET.get("threshold", 0.6))
        limit     = min(int(request.GET.get("limit", 20)), 100)
 
        claims = Claim.objects.filter(
            fraud_score__gte=threshold
        ).select_related("policy", "policy__policyholder", "policy__vehicle")[:limit]
 
        results = [{
            "claim_id":          str(c.id),
            "claim_number":      str(c.claim_number),
            "claimed_amount":    float(c.claimed_amount),
            "claim_type":        str(c.claim_type),
            "severity":          str(c.severity),
            "fraud_probability": round(float(c.fraud_score or 0), 4),
            "submitted_date":    c.submitted_date.isoformat(),
            "policyholder_name": f"{c.policy.policyholder.first_name} {c.policy.policyholder.last_name}",
        } for c in claims]
 
        return Response({"count": len(results), "threshold": threshold, "results": results})
 
    except Exception as exc:
        return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
 
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def fraud_statistics(request):
    """Aggregate fraud statistics across all claims."""
    try:
        total_claims      = Claim.objects.count()
        fraudulent_claims = Claim.objects.filter(is_fraudulent=True).count()
        high_fraud_score  = Claim.objects.filter(fraud_score__gte=0.7).count()
        fraud_rate        = fraudulent_claims / total_claims if total_claims > 0 else 0
        avg_fraud_score   = Claim.objects.aggregate(Avg("fraud_score"))["fraud_score__avg"] or 0
 
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
            "total_claims":       total_claims,
            "fraudulent_claims":  fraudulent_claims,
            "high_risk_claims":   high_fraud_score,
            "fraud_rate":         round(fraud_rate, 4),
            "average_fraud_score": round(avg_fraud_score, 4),
            "by_claim_type":      by_claim_type,
            "by_severity":        by_severity,
            "generated_at":       timezone.now().isoformat(),
        })
 
    except Exception as exc:
        return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)