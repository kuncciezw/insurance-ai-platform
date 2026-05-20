"""
system_settings/serializers.py

Serializer for GlobalPricingSettings with cross-field validation
so the admin can't accidentally save a broken configuration through
the API (the Django admin form is a separate layer).
"""

from decimal import Decimal
from rest_framework import serializers
from .models import GlobalPricingSettings


class GlobalPricingSettingsSerializer(serializers.ModelSerializer):

    class Meta:
        model = GlobalPricingSettings
        fields = '__all__'

    # ── Field-level validation ────────────────────────────────────────────

    def validate_threshold_fraud_reject(self, value: float) -> float:
        if not 0.0 <= value <= 1.0:
            raise serializers.ValidationError(
                "Fraud reject threshold must be between 0.0 and 1.0."
            )
        return value

    def validate_threshold_variance_warning(self, value: float) -> float:
        if not 0.0 <= value <= 1.0:
            raise serializers.ValidationError(
                "Variance warning threshold must be between 0.0 and 1.0."
            )
        return value

    def validate_zwg_usd_exchange_rate(self, value: Decimal) -> Decimal:
        if value <= Decimal('0'):
            raise serializers.ValidationError(
                "Exchange rate must be a positive number."
            )
        return value

    # ── Cross-field validation ────────────────────────────────────────────

    def validate(self, data: dict) -> dict:
        # 1. fraud_reject must be strictly greater than variance_warning
        reject = data.get(
            'threshold_fraud_reject',
            self.instance.threshold_fraud_reject if self.instance else 0.50
        )
        warning = data.get(
            'threshold_variance_warning',
            self.instance.threshold_variance_warning if self.instance else 0.20
        )
        if reject <= warning:
            raise serializers.ValidationError({
                'threshold_fraud_reject': (
                    "Fraud reject threshold must be higher than the variance "
                    "warning threshold."
                )
            })

        # 2. auto_approve must be less than manual_review
        auto = data.get(
            'threshold_auto_approve',
            self.instance.threshold_auto_approve if self.instance else Decimal('1000')
        )
        manual = data.get(
            'threshold_manual_review',
            self.instance.threshold_manual_review if self.instance else Decimal('5000')
        )
        if auto >= manual:
            raise serializers.ValidationError({
                'threshold_auto_approve': (
                    "Auto-approve threshold must be lower than the manual "
                    "review threshold."
                )
            })

        # 3. Cost-breakdown ratios should sum to 1.0 (warn, don't hard-fail)
        ratio_fields = [
            'ratio_vehicle_damage',
            'ratio_medical_expenses',
            'ratio_legal_fees',
            'ratio_other_costs',
        ]
        ratios = [
            data.get(f, getattr(self.instance, f, Decimal('0')))
            for f in ratio_fields
        ]
        ratio_sum = sum(ratios)
        if abs(ratio_sum - Decimal('1.00')) > Decimal('0.01'):
            raise serializers.ValidationError(
                f"Cost-breakdown ratios must sum to 1.00 (currently {ratio_sum})."
            )

        return data