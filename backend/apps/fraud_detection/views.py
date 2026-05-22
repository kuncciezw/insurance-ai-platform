from __future__ import annotations

from datetime import timedelta
import logging
import os
from typing import Type

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.serializers import BaseSerializer
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone

from google import genai
from google.genai import types
from django.conf import settings

from .models import Policyholder, Vehicle, Policy, Claim
from .serializers import (
    PolicyholderSerializer, PolicyholderListSerializer,
    VehicleSerializer, VehicleListSerializer,
    PolicySerializer, PolicyListSerializer,
    ClaimSerializer, ClaimListSerializer,
    ClaimFraudAnalysisSerializer,
)

logger = logging.getLogger(__name__)

_GEMINI_KEY: str = getattr(settings, "GEMINI_API_KEY", None) or os.environ.get("GEMINI_API_KEY", "")
if not _GEMINI_KEY:
    logger.warning("GEMINI_API_KEY is not set — /api/ai/explain-claim/ will not work.")


class PolicyholderViewSet(viewsets.ModelViewSet):
    queryset = Policyholder.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["gender", "marital_status", "occupation", "is_active", "state", "city", "credit_rating"]
    search_fields = ["first_name", "last_name", "email", "policy_holder_id", "phone_number"]
    ordering_fields = ["created_at", "last_name", "credit_score", "monthly_income"]
    ordering = ["-created_at"]

    def get_serializer_class(self) -> Type[BaseSerializer]:
        if self.action == "list":
            return PolicyholderListSerializer
        return PolicyholderSerializer

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        return [IsAuthenticated()]

    @action(detail=True, methods=["get"])
    def policies(self, request, pk=None):
        policyholder = self.get_object()
        serializer = PolicyListSerializer(policyholder.policies.all(), many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def vehicles(self, request, pk=None):
        policyholder = self.get_object()
        serializer = VehicleListSerializer(policyholder.vehicles.all(), many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def claims(self, request, pk=None):
        policyholder = self.get_object()
        serializer = ClaimListSerializer(policyholder.claims.all(), many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def statistics(self, request, pk=None):
        policyholder = self.get_object()
        stats = {
            "total_policies": policyholder.policies.count(),
            "active_policies": policyholder.policies.filter(status="ACTIVE").count(),
            "total_vehicles": policyholder.vehicles.count(),
            "total_claims": policyholder.claims.count(),
            "pending_claims": policyholder.claims.filter(claim_status="SUBMITTED").count(),
            "approved_claims": policyholder.claims.filter(claim_status="APPROVED").count(),
            "total_claimed_amount": policyholder.claims.aggregate(total=Sum("claimed_amount"))["total"] or 0,
            "fraudulent_claims": policyholder.claims.filter(is_fraudulent=True).count(),
        }
        return Response(stats)

    @action(detail=False, methods=["get"])
    def high_risk(self, request):
        high_risk_holders = Policyholder.objects.filter(
            Q(credit_score__lt=600)
            | Q(claims__is_fraudulent=True)
            | Q(has_driving_license=False)
            | Q(is_medical_license_valid=False)
        ).distinct()
        serializer = self.get_serializer(high_risk_holders, many=True)
        return Response(serializer.data)


class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.select_related("policyholder").all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["vehicle_type", "fuel_type", "manufacture_year", "make", "has_anti_theft", "is_modified"]
    search_fields = ["vin", "registration_number", "make", "model"]
    ordering_fields = ["created_at", "manufacture_year", "market_value", "odometer_reading"]
    ordering = ["-created_at"]
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self) -> Type[BaseSerializer]:
        if self.action == "list":
            return VehicleListSerializer
        return VehicleSerializer

    @action(detail=True, methods=["get"])
    def policies(self, request, pk=None):
        vehicle = self.get_object()
        serializer = PolicyListSerializer(vehicle.policies.all(), many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def claims(self, request, pk=None):
        vehicle = self.get_object()
        serializer = ClaimListSerializer(vehicle.claims.all(), many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def high_value(self, request):
        from system_settings.models import GlobalPricingSettings
        threshold = GlobalPricingSettings.get_solo().threshold_manual_review
        high_value_claims = Claim.objects.filter(claimed_amount__gt=threshold)
        serializer = self.get_serializer(high_value_claims, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def modified_vehicles(self, request):
        modified = Vehicle.objects.filter(is_modified=True)
        serializer = self.get_serializer(modified, many=True)
        return Response(serializer.data)


class PolicyViewSet(viewsets.ModelViewSet):
    queryset = Policy.objects.select_related("policyholder", "vehicle").all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "policy_type", "coverage_level", "currency"]
    search_fields = ["policy_number", "policyholder__first_name", "policyholder__last_name"]
    ordering_fields = ["created_at", "start_date", "end_date", "premium_amount"]
    ordering = ["-created_at"]
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self) -> Type[BaseSerializer]:
        if self.action == "list":
            return PolicyListSerializer
        return PolicySerializer

    @action(detail=True, methods=["get"])
    def claims(self, request, pk=None):
        policy = self.get_object()
        serializer = ClaimListSerializer(policy.claims.all(), many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def active(self, request):
        serializer = self.get_serializer(Policy.objects.filter(status="ACTIVE"), many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def expiring_soon(self, request):
        today = timezone.now().date()
        expiring = Policy.objects.filter(
            status="ACTIVE",
            end_date__gte=today,
            end_date__lte=today + timedelta(days=30),
        )
        serializer = self.get_serializer(expiring, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def renew(self, request, pk=None):
        policy = self.get_object()
        if policy.status not in ("ACTIVE", "EXPIRED"):
            return Response(
                {"error": "Only active or expired policies can be renewed"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        new_policy = Policy.objects.create(
            policy_number=f"POL-{timezone.now().timestamp()}",
            policyholder=policy.policyholder,
            vehicle=policy.vehicle,
            policy_type=policy.policy_type,
            coverage_level=policy.coverage_level,
            status="PENDING",
            currency=policy.currency,
            start_date=policy.end_date,
            end_date=policy.end_date + timedelta(days=365),
            has_roadside_assistance=policy.has_roadside_assistance,
            has_rental_coverage=policy.has_rental_coverage,
            has_glass_coverage=policy.has_glass_coverage,
        )
        serializer = self.get_serializer(new_policy)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def statistics(self, request):
        stats = {
            "total_policies": Policy.objects.count(),
            "active_policies": Policy.objects.filter(status="ACTIVE").count(),
            "expired_policies": Policy.objects.filter(status="EXPIRED").count(),
            "cancelled_policies": Policy.objects.filter(status="CANCELLED").count(),
            "total_premium_value": Policy.objects.filter(status="ACTIVE").aggregate(total=Sum("premium_amount"))["total"] or 0,
            "average_premium": Policy.objects.filter(status="ACTIVE").aggregate(avg=Avg("premium_amount"))["avg"] or 0,
            "policies_by_type": dict(
                Policy.objects.values("policy_type").annotate(count=Count("id")).values_list("policy_type", "count")
            ),
        }
        return Response(stats)


class ClaimViewSet(viewsets.ModelViewSet):
    queryset = Claim.objects.select_related("policy", "policyholder", "vehicle").all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["claim_status", "claim_type", "severity", "is_fraudulent", "payment_method"]
    search_fields = ["claim_number", "policyholder__first_name", "policyholder__last_name"]
    ordering_fields = ["submitted_date", "incident_date", "claimed_amount", "fraud_score", "claim_status"]
    ordering = ["-submitted_date"]
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self) -> Type[BaseSerializer]:
        if self.action == "list":
            return ClaimListSerializer
        if self.action == "fraud_analysis":
            return ClaimFraudAnalysisSerializer
        return ClaimSerializer

    @action(detail=False, methods=["get"])
    def pending(self, request):
        pending_claims = Claim.objects.filter(claim_status__in=["SUBMITTED", "UNDER_REVIEW"])
        serializer = self.get_serializer(pending_claims, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def fraudulent(self, request):
        from system_settings.models import GlobalPricingSettings
        threshold = GlobalPricingSettings.get_solo().threshold_fraud_reject
        fraudulent_claims = Claim.objects.filter(Q(is_fraudulent=True) | Q(fraud_score__gte=threshold))
        serializer = self.get_serializer(fraudulent_claims, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def high_value(self, request):
        from system_settings.models import GlobalPricingSettings
        threshold = GlobalPricingSettings.get_solo().threshold_manual_review
        high_value_claims = Claim.objects.filter(claimed_amount__gt=threshold)
        serializer = self.get_serializer(high_value_claims, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        claim = self.get_object()
        if claim.claim_status not in ("SUBMITTED", "UNDER_REVIEW"):
            return Response(
                {"error": "Only submitted or under review claims can be approved"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        claim.claim_status = "APPROVED"
        claim.approved_amount = request.data.get("approved_amount", claim.claimed_amount)
        claim.reviewed_date = timezone.now()
        claim.save()
        return Response(self.get_serializer(claim).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        claim = self.get_object()
        if claim.claim_status not in ("SUBMITTED", "UNDER_REVIEW"):
            return Response(
                {"error": "Only submitted or under review claims can be rejected"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        claim.claim_status = "REJECTED"
        claim.fraud_reason = request.data.get("reason", "No reason provided")
        claim.reviewed_date = timezone.now()
        claim.save()
        return Response(self.get_serializer(claim).data)

    @action(detail=True, methods=["post"])
    def mark_paid(self, request, pk=None):
        claim = self.get_object()
        if claim.claim_status != "APPROVED":
            return Response(
                {"error": "Only approved claims can be marked as paid"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        claim.claim_status = "PAID"
        claim.paid_amount = request.data.get("paid_amount", claim.approved_amount)
        claim.save()
        return Response(self.get_serializer(claim).data)

    @action(detail=True, methods=["get"])
    def fraud_analysis(self, request, pk=None):
        claim = self.get_object()
        serializer = ClaimFraudAnalysisSerializer(claim)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def statistics(self, request):
        stats = {
            "total_claims": Claim.objects.count(),
            "pending_claims": Claim.objects.filter(claim_status__in=["SUBMITTED", "UNDER_REVIEW"]).count(),
            "approved_claims": Claim.objects.filter(claim_status="APPROVED").count(),
            "rejected_claims": Claim.objects.filter(claim_status="REJECTED").count(),
            "paid_claims": Claim.objects.filter(claim_status="PAID").count(),
            "fraudulent_claims": Claim.objects.filter(is_fraudulent=True).count(),
            "total_claimed_amount": Claim.objects.aggregate(total=Sum("claimed_amount"))["total"] or 0,
            "total_approved_amount": Claim.objects.aggregate(total=Sum("approved_amount"))["total"] or 0,
            "total_paid_amount": Claim.objects.aggregate(total=Sum("paid_amount"))["total"] or 0,
            "average_claim_amount": Claim.objects.aggregate(avg=Avg("claimed_amount"))["avg"] or 0,
            "claims_by_type": dict(
                Claim.objects.values("claim_type").annotate(count=Count("id")).values_list("claim_type", "count")
            ),
            "claims_by_status": dict(
                Claim.objects.values("claim_status").annotate(count=Count("id")).values_list("claim_status", "count")
            ),
        }
        return Response(stats)

    @action(detail=False, methods=["get"])
    def recent_activity(self, request):
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_claims = Claim.objects.filter(submitted_date__gte=thirty_days_ago).order_by("-submitted_date")[:50]
        serializer = self.get_serializer(recent_claims, many=True)
        return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def explain_claim(request):
    gemini_key = getattr(settings, "GEMINI_API_KEY", None) or os.environ.get("GEMINI_API_KEY", "")

    if not gemini_key:
        return Response(
            {"error": "AI explanation service is not configured on this server."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    data = request.data
    claim = data.get("claim", {})
    policyholder = data.get("policyholder", {})
    vehicle = data.get("vehicle", {})
    policy = data.get("policy", {})
    fraud_analysis = data.get("fraud_analysis", {})
    currency = data.get("currency", "USD")

    prompt = _build_prompt(claim, policyholder, vehicle, policy, fraud_analysis, currency)

    try:
        client = genai.Client(api_key=gemini_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=3000,
                temperature=0.15,
            ),
        )
        return Response({"explanation": (response.text or "").strip()})

    except Exception as exc:
        logger.exception("Gemini call failed for claim %s", claim.get("claim_number"))
        return Response(
            {"error": f"AI service error: {exc}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def _build_prompt(claim, policyholder, vehicle, policy, fraud_analysis, currency):
    from datetime import datetime, timezone as tz, date

    def fmt(v):
        try:
            return f"{currency} {float(v):,.2f}"
        except (TypeError, ValueError):
            return str(v or "—")

    def parse_dt(s):
        if not s:
            return None
        try:
            dt = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=tz.utc)
            return dt
        except Exception:
            return None

    incident_dt  = parse_dt(claim.get("incident_date"))
    submitted_dt = parse_dt(claim.get("submitted_date"))
    policy_start = parse_dt(policy.get("start_date"))

    days_since_start = (
        round((incident_dt - policy_start).total_seconds() / 86400)
        if incident_dt and policy_start else None
    )
    delay_hours = (
        round((submitted_dt - incident_dt).total_seconds() / 3600)
        if submitted_dt and incident_dt else None
    )

    claimed  = float(claim.get("claimed_amount") or 0)
    coverage = float(policy.get("coverage_amount") or 1)
    cov_ratio = f"{(claimed / coverage * 100):.1f}%" if coverage else "?"

    current_year = date.today().year
    veh_year = vehicle.get("manufacture_year")
    veh_age  = (current_year - int(veh_year)) if veh_year else None

    model_exp   = fraud_analysis.get("model_explanation", {})
    risk_up     = model_exp.get("risk_increasers", [])
    risk_down   = model_exp.get("risk_decreasers", [])
    fraud_data  = fraud_analysis.get("fraud_analysis", {})
    doc_flags   = fraud_data.get("document_flags", [])
    risk_signals = [
        f for f in (fraud_analysis.get("risk_factors") or [])
        if f != "No significant risk factors detected"
    ]

    def fmt_features(lst):
        if not lst:
            return "  (none)"
        lines = []
        for f in lst:
            label  = f.get("label") or f.get("feature") or "?"
            weight = f.get("impact_weight") or 0.0
            reason = f.get("reason") or ""
            sign   = "+" if weight > 0 else ""
            lines.append(f"  * {label} | SHAP {sign}{weight:.4f} | {reason}")
        return "\n".join(lines)

    delay_str    = f"{delay_hours} hours" if delay_hours is not None else "Unknown"
    days_str     = f"{days_since_start} days" if days_since_start is not None else "Unknown"
    incident_str = incident_dt.strftime("%d %b %Y %H:%M") if incident_dt else "Unknown"
    veh_desc     = f"{veh_year} {vehicle.get('make', '')} {vehicle.get('model', '')}"
    if veh_age:
        veh_desc += f" ({veh_age} years old)"
    doc_block = "\n".join(f"  * {f}" for f in doc_flags)   if doc_flags   else "  None raised."
    sig_block = "\n".join(f"  * {f}" for f in risk_signals) if risk_signals else "  None flagged."
    claim_type = claim.get("claim_type", "this type of")
    verdict    = str(claim.get("claim_status", "UNKNOWN")).upper()

    # ── Verdict-aware framing so Gemini defends the decision, never fights it ──
    if verdict == "APPROVED":
        verdict_stance = (
            "The system has APPROVED this claim. Your job is to clearly and confidently explain "
            "WHY the system approved it — what factors justified that decision. Where risk factors "
            "exist, you must frame them as 'areas for the adjuster to monitor going forward' or "
            "'conditions that were weighed and found insufficient to override approval', NOT as "
            "evidence that the system made a mistake. Never use words like 'despite', 'however', "
            "'although', or 'nevertheless' in a way that implies the approval was wrong or surprising."
        )
    elif verdict == "REJECTED":
        verdict_stance = (
            "The system has REJECTED this claim. Your job is to clearly and confidently explain "
            "WHY the system rejected it — what specific factors drove that decision. Where factors "
            "exist that speak in favour of the claimant, frame them as 'mitigating considerations "
            "the adjuster should weigh if they choose to override', NOT as evidence that the "
            "rejection was wrong. Never imply the system erred."
        )
    else:
        verdict_stance = (
            f"The system verdict is {verdict}. Explain the factors that led to this outcome "
            "confidently and without implying the system made an error."
        )

    combined_pct  = float(claim.get("fraud_score") or 0) * 100
    ml_pct        = float(fraud_data.get("ml_score") or 0) * 100
    doc_leg_raw   = fraud_data.get("document_legitimacy")
    doc_leg_pct   = f"{float(doc_leg_raw) * 100:.1f}%" if doc_leg_raw is not None else "Not available (no evidence uploaded)"

    return (
        "ROLE\n"
        "You are a senior insurance fraud analyst producing a formal written assessment for a "
        "claims adjuster. Your analysis must be authoritative, data-grounded, and aligned with "
        "the system verdict — you are here to EXPLAIN and JUSTIFY the system's decision, not to "
        "audit or second-guess it.\n\n"

        f"VERDICT ALIGNMENT RULE\n"
        f"{verdict_stance}\n\n"

        "WRITING RULES — ENFORCE STRICTLY\n"
        "1. Write EXACTLY 6 paragraphs, one per section in REQUIRED OUTPUT STRUCTURE below.\n"
        "2. Every paragraph must contain a MINIMUM of 5 sentences.\n"
        "3. Every sentence must reference at least one specific value, date, score, amount, "
        "or named field from the DATA BLOCK — no generic filler sentences are permitted.\n"
        "4. Do NOT use bullet points, numbered lists, or section headings inside your response.\n"
        "5. Do NOT use the words 'despite', 'however', 'although', or 'nevertheless' to "
        "introduce doubt about the verdict.\n"
        "6. Risk factors and negative signals must be framed as monitoring notes or context, "
        "not as contradictions to the verdict.\n"
        "7. For PARAGRAPH 5, name and explain EVERY SHAP feature individually — do not group "
        "or skip any.\n"
        "8. Minimum total output: 500 words.\n\n"

        "DATA BLOCK\n"
        "----------\n"
        f"CLAIM\n"
        f"  Claim number          : {claim.get('claim_number', 'N/A')}\n"
        f"  Claim type            : {claim_type}\n"
        f"  Severity              : {claim.get('severity', 'N/A')}\n"
        f"  Incident date         : {incident_str}\n"
        f"  Incident location     : {claim.get('incident_location', 'Unknown')}\n"
        f"  Vehicles involved     : {claim.get('number_of_vehicles_involved', 1)}\n"
        f"  Claimed amount        : {fmt(claimed)}\n"
        f"  Policy coverage limit : {fmt(coverage)}\n"
        f"  Claim-to-coverage     : {cov_ratio} of the policy limit\n"
        f"  AUTOMATED VERDICT     : {verdict}\n"
        f"  Combined fraud score  : {combined_pct:.1f}%  (ML 65% weight + Document 35% weight)\n"
        f"  ML model score        : {ml_pct:.1f}%\n"
        f"  Document legitimacy   : {doc_leg_pct}\n"
        f"  Days policy to incident  : {days_str}\n"
        f"  Hours incident to filed  : {delay_str}\n\n"
        f"POLICYHOLDER\n"
        f"  Age                   : {policyholder.get('age', 'Unknown')} years\n"
        f"  Occupation            : {policyholder.get('occupation', 'Unknown')}\n"
        f"  Credit score          : {policyholder.get('credit_score', 'Unknown')} "
        f"({str(policyholder.get('credit_rating', '')).replace('_', ' ')})\n"
        f"  Years with company    : {policyholder.get('years_with_company', 0)}\n"
        f"  Valid driving licence : {'Yes' if policyholder.get('has_driving_license') else 'No'}\n"
        f"  Defensive licence     : {'Yes' if policyholder.get('has_defensive_license') else 'No'}\n"
        f"  Medical fitness valid : {'Yes' if policyholder.get('is_medical_license_valid') else 'No'}\n\n"
        f"VEHICLE\n"
        f"  Description  : {veh_desc}\n"
        f"  Market value : {fmt(vehicle.get('market_value'))}\n"
        f"  Anti-theft   : {'Yes' if vehicle.get('has_anti_theft') else 'No'}\n"
        f"  Modified     : {'Yes' if vehicle.get('is_modified') else 'No'}\n\n"
        f"POLICY\n"
        f"  Type           : {policy.get('policy_type', 'N/A')}\n"
        f"  Coverage level : {policy.get('coverage_level', 'N/A')}\n"
        f"  Start date     : {policy.get('start_date', 'Unknown')}\n"
        f"  Premium        : {fmt(policy.get('premium_amount'))}\n\n"
        f"ML SHAP FEATURES THAT RAISED THE FRAUD SCORE\n"
        f"{fmt_features(risk_up)}\n\n"
        f"ML SHAP FEATURES THAT LOWERED THE FRAUD SCORE\n"
        f"{fmt_features(risk_down)}\n\n"
        f"DOCUMENT FLAGS\n"
        f"{doc_block}\n\n"
        f"SYSTEM RISK SIGNALS\n"
        f"{sig_block}\n\n"

        "REQUIRED OUTPUT STRUCTURE\n"
        "Write exactly these 6 paragraphs in order. No headings. No bullets. "
        "Minimum 5 sentences each. Minimum 500 words total.\n\n"

        f"PARAGRAPH 1 — VERDICT JUSTIFICATION\n"
        f"Open by stating the automated verdict ({verdict}) and the combined fraud score of "
        f"{combined_pct:.1f}% clearly and confidently. Explain the two-component scoring "
        f"model: the ML model contributed {ml_pct:.1f}% and the document legitimacy component "
        f"contributed {doc_leg_pct}, weighted 65%/35% respectively. Explain what the combined "
        f"score of {combined_pct:.1f}% means in absolute terms — where it sits relative to "
        "approval and rejection thresholds. State the claim type, severity level, and exact "
        f"claimed amount of {fmt(claimed)}. Conclude by confirming that the verdict is consistent "
        "with these inputs and explain the primary reason the system reached this conclusion.\n\n"

        f"PARAGRAPH 2 — CLAIM TIMELINE AND FINANCIAL EXPOSURE\n"
        f"Explain that the incident occurred {days_str} after policy inception and analyse "
        "whether this window raises or lowers concern — reference industry norms for early "
        "claims and whether this specific gap is within normal bounds. Discuss the filing "
        f"delay of {delay_str} from incident to submission and whether that is consistent "
        f"with standard behaviour for a {claim_type} claim of {claim.get('severity', 'N/A')} "
        f"severity. State that the claimed amount of {fmt(claimed)} represents {cov_ratio} of "
        f"the {fmt(coverage)} policy coverage limit and assess whether that ratio is typical, "
        "elevated, or conservative for this claim type. Explain how the timeline and financial "
        "exposure data together contributed to the verdict. Close with a statement on whether "
        "the financial exposure is within a range the system considers manageable.\n\n"

        "PARAGRAPH 3 — POLICYHOLDER RISK PROFILE\n"
        f"Discuss the policyholder's credit score of {policyholder.get('credit_score', 'Unknown')} "
        f"({str(policyholder.get('credit_rating', '')).replace('_', ' ')}) and what it "
        "indicates about financial stability and the likelihood of opportunistic fraud. "
        f"Analyse the {policyholder.get('years_with_company', 0)} years of relationship history "
        "with the company and how customer tenure affects trust weighting in the model. "
        f"Note the occupation ({policyholder.get('occupation', 'Unknown')}) and whether it "
        f"carries any risk relevance to a {claim_type} claim. Assess the driving licence status "
        f"({'valid' if policyholder.get('has_driving_license') else 'absent'}), defensive driving "
        f"licence ({'held' if policyholder.get('has_defensive_license') else 'not held'}), and "
        f"medical fitness certificate ({'valid' if policyholder.get('is_medical_license_valid') else 'invalid'}) "
        f"— explain whether any of these statuses are directly material to a {claim_type} claim. "
        "Conclude with an overall assessment of the policyholder profile and how it contributed "
        "to the verdict.\n\n"

        "PARAGRAPH 4 — VEHICLE ASSESSMENT\n"
        f"Describe the insured vehicle ({veh_desc}) in full and state its market value of "
        f"{fmt(vehicle.get('market_value'))}. Assess whether the claimed amount of {fmt(claimed)} "
        "is proportionate, conservative, or elevated relative to the vehicle's market value — "
        "cite the specific ratio. Evaluate the relevance of the anti-theft device status "
        f"({'installed' if vehicle.get('has_anti_theft') else 'not installed'}) to a "
        f"{claim_type} claim specifically and whether its presence or absence is a meaningful "
        "risk signal in this context. Assess whether the vehicle's modification status "
        f"({'modified' if vehicle.get('is_modified') else 'unmodified'}) introduces any "
        "additional valuation or fraud risk. Close with a statement on whether the vehicle "
        "profile is consistent with the claimed loss.\n\n"

        "PARAGRAPH 5 — ML MODEL SHAP FEATURE ANALYSIS\n"
        "This paragraph must discuss every single SHAP feature listed — do not group, "
        "summarise, or skip any. For each feature under 'ML SHAP FEATURES THAT RAISED THE "
        "FRAUD SCORE': state the feature name, its exact SHAP weight, and explain in plain "
        "English what that feature represents and why a high value for it pushes the fraud "
        "score upward for this specific claim. For each feature under 'ML SHAP FEATURES THAT "
        "LOWERED THE FRAUD SCORE': state the feature name, its exact SHAP weight, and explain "
        "why that feature reduced the risk score. If one list is empty, explicitly say so. "
        "Conclude by describing the net balance of SHAP signals — whether risk-increasing or "
        "risk-reducing features dominate — and how the net SHAP outcome aligns with the verdict.\n\n"

        "PARAGRAPH 6 — DOCUMENT ANALYSIS, SYSTEM SIGNALS AND ADJUSTER RECOMMENDATION\n"
        f"State the document legitimacy score of {doc_leg_pct} and explain what it means. "
        "Work through every document flag raised one by one, explaining what each flag means "
        "and what action, if any, it warrants — or explicitly state that no document flags "
        "were raised. Work through every system risk signal one by one in the same way — or "
        "explicitly state that none were flagged. Based on the combined fraud score, SHAP "
        "analysis, policyholder profile, vehicle assessment, timeline, and document analysis, "
        f"provide a clear adjuster recommendation: confirm the {verdict} verdict, request "
        "additional documentation, escalate for investigation, or override — and state the "
        "specific scores, thresholds, and factors that support that recommendation. Close "
        "with a concrete statement of what the adjuster's next action should be and the "
        "rationale behind it."
    )

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def fraud_statistics_chart(request):
    from system_settings.models import GlobalPricingSettings

    period = request.query_params.get("period", "30days")
    today = timezone.now().date()

    if period == "7days":
        start_date = today - timedelta(days=7)
    elif period == "30days":
        start_date = today - timedelta(days=30)
    elif period == "90days":
        start_date = today - timedelta(days=90)
    else:
        start_date = today - timedelta(days=365)

    cfg = GlobalPricingSettings.get_solo()
    warn_thresh = float(cfg.threshold_variance_warning)
    reject_thresh = float(cfg.threshold_fraud_reject)

    claims = Claim.objects.filter(submitted_date__date__gte=start_date)

    low_risk = claims.filter(fraud_score__lt=warn_thresh).count()
    medium_risk = claims.filter(fraud_score__gte=warn_thresh, fraud_score__lt=reject_thresh).count()
    high_risk = claims.filter(fraud_score__gte=reject_thresh).count()
    total = low_risk + medium_risk + high_risk

    if total == 0:
        return Response({
            "low_risk": 0, "medium_risk": 0, "high_risk": 0,
            "fraud_rate": 0,
            "low_risk_percentage": 0,
            "medium_risk_percentage": 0,
            "high_risk_percentage": 0,
            "period": period,
            "total_claims": 0,
            "thresholds": {
                "low_medium_boundary": warn_thresh,
                "medium_high_boundary": reject_thresh,
            },
        })

    return Response({
        "low_risk": low_risk,
        "medium_risk": medium_risk,
        "high_risk": high_risk,
        "fraud_rate": round(high_risk / total * 100, 1),
        "low_risk_percentage": round(low_risk / total * 100, 1),
        "medium_risk_percentage": round(medium_risk / total * 100, 1),
        "high_risk_percentage": round(high_risk / total * 100, 1),
        "period": period,
        "total_claims": total,
        "thresholds": {
            "low_medium_boundary": warn_thresh,
            "medium_high_boundary": reject_thresh,
        },
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def claims_activity_chart(request):
    period = request.query_params.get("period", "12months")
    today = timezone.now().date()

    if period == "7days":
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        data = []
        for i in range(7):
            d = today - timedelta(days=6 - i)
            count = Claim.objects.filter(submitted_date__date=d).count()
            data.append({"label": days[d.weekday()], "count": count})

    elif period == "30days":
        data = []
        for i in range(4):
            start_date = today - timedelta(days=(4 - i) * 7)
            end_date = start_date + timedelta(days=7)
            count = Claim.objects.filter(
                submitted_date__date__gte=start_date,
                submitted_date__date__lt=end_date,
            ).count()
            data.append({"label": f"Week {i + 1}", "count": count})

    elif period == "12months":
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        data = []
        for i in range(12):
            month_date = today.replace(day=1) - timedelta(days=1)
            for _ in range(10 - i):
                month_date = month_date.replace(day=1) - timedelta(days=1)
            count = Claim.objects.filter(
                submitted_date__year=month_date.year,
                submitted_date__month=month_date.month,
            ).count()
            data.append({"label": months[month_date.month - 1], "count": count})

    else:
        data = []
        for i in range(4):
            quarter_start = today - timedelta(days=365) + timedelta(days=i * 91)
            quarter_end = quarter_start + timedelta(days=91)
            count = Claim.objects.filter(
                submitted_date__date__gte=quarter_start,
                submitted_date__date__lt=quarter_end,
            ).count()
            data.append({"label": f"Q{i + 1}", "count": count})

    return Response(data)