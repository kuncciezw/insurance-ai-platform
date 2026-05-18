"""
Django REST Framework Serializers for Claims Automation models
"""

from rest_framework import serializers
from .models import ClaimEstimate, ClaimProcessingLog
from apps.fraud_detection.models import Claim
from decimal import Decimal


class ClaimEstimateSerializer(serializers.ModelSerializer):
    """Full serializer for ClaimEstimate model"""

    claim_number = serializers.CharField(source='claim.claim_number', read_only=True)
    claim_type = serializers.CharField(source='claim.claim_type', read_only=True)
    claimed_amount = serializers.DecimalField(
        source='claim.claimed_amount',
        max_digits=12,
        decimal_places=2,
        read_only=True
    )
    variance_percentage = serializers.ReadOnlyField()
    is_within_tolerance = serializers.ReadOnlyField()
    needs_review = serializers.ReadOnlyField()

    class Meta:
        model = ClaimEstimate
        fields = [
            'id', 'estimate_number', 'claim', 'claim_number', 'claim_type',
            'claimed_amount', 'estimated_cost', 'confidence_score',
            'confidence_lower_bound', 'confidence_upper_bound',
            'predicted_severity', 'severity_score', 'recommended_reserve',
            'reserve_adequacy_ratio', 'processing_recommendation',
            'triage_priority', 'estimated_processing_days', 'cost_breakdown',
            'risk_factors', 'actual_settlement_amount', 'prediction_accuracy',
            'variance_percentage', 'is_within_tolerance', 'needs_review',
            'model_version', 'features_used', 'manual_adjustment',
            'adjustment_reason', 'adjusted_by', 'final_estimate',
            'created_at', 'updated_at', 'reviewed_at'
        ]
        read_only_fields = [
            'id', 'estimate_number', 'created_at', 'updated_at',
            'variance_percentage', 'is_within_tolerance', 'needs_review'
        ]

    def validate_manual_adjustment(self, value):
        """Validate manual adjustment is reasonable"""
        if abs(value) > Decimal('50000.00'):
            raise serializers.ValidationError(
                "Manual adjustment cannot exceed $50,000"
            )
        return value


class ClaimEstimateListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing estimates"""

    claim_number = serializers.CharField(source='claim.claim_number', read_only=True)
    claim_type = serializers.CharField(source='claim.claim_type', read_only=True)
    needs_review = serializers.ReadOnlyField()

    class Meta:
        model = ClaimEstimate
        fields = [
            'id', 'estimate_number', 'claim_number', 'claim_type',
            'estimated_cost', 'predicted_severity', 'triage_priority',
            'processing_recommendation', 'confidence_score', 'needs_review',
            'created_at'
        ]


class ClaimEstimateInputSerializer(serializers.Serializer):
    """Serializer for claim cost estimation input"""

    claim_id = serializers.UUIDField(required=True)

    # Optional overrides for what-if analysis
    override_severity = serializers.ChoiceField(
        choices=['MINOR', 'MODERATE', 'MAJOR', 'CRITICAL'],
        required=False
    )
    # REMOVED: override_injuries — field deleted from Claim model
    # REMOVED: override_vehicles — no longer part of what-if analysis

    def validate_claim_id(self, value):
        """Validate that claim exists"""
        try:
            Claim.objects.get(id=value)
        except Claim.DoesNotExist:
            raise serializers.ValidationError("Claim not found")
        return value


class ClaimProcessingLogSerializer(serializers.ModelSerializer):
    """Full serializer for ClaimProcessingLog model"""

    claim_number = serializers.CharField(source='claim.claim_number', read_only=True)
    estimate_number = serializers.CharField(
        source='estimate.estimate_number',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = ClaimProcessingLog
        fields = [
            'id', 'claim', 'claim_number', 'estimate', 'estimate_number',
            'action_type', 'action_description', 'is_automated',
            'performed_by', 'result_data', 'previous_value', 'new_value',
            'processing_time_ms', 'model_version', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ClaimProcessingLogListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing processing logs"""

    claim_number = serializers.CharField(source='claim.claim_number', read_only=True)

    class Meta:
        model = ClaimProcessingLog
        fields = [
            'id', 'claim_number', 'action_type', 'is_automated',
            'performed_by', 'created_at'
        ]


class ClaimTriageInputSerializer(serializers.Serializer):
    """Serializer for batch claim triage input"""

    claim_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100
    )

    def validate_claim_ids(self, value):
        """Validate that all claims exist"""
        existing_ids = set(Claim.objects.filter(id__in=value).values_list('id', flat=True))
        invalid_ids = set(value) - existing_ids

        if invalid_ids:
            raise serializers.ValidationError(
                f"Claims not found: {', '.join(str(id) for id in invalid_ids)}"
            )

        return value


class EstimateUpdateSerializer(serializers.Serializer):
    """Serializer for updating estimate with actual settlement"""

    actual_settlement_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.00'),
        required=True
    )
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate_actual_settlement_amount(self, value):
        """Validate settlement amount is reasonable"""
        if value > Decimal('1000000.00'):
            raise serializers.ValidationError(
                "Settlement amount exceeds maximum allowed ($1,000,000)"
            )
        return value