"""
Django REST Framework Serializers for Dynamic Pricing models
"""

from rest_framework import serializers
from .models import Quote, PriceHistory
from apps.fraud_detection.models import Policyholder, Vehicle, Policy
from datetime import date, timedelta
from decimal import Decimal


class QuoteSerializer(serializers.ModelSerializer):
    """Serializer for Quote model"""

    is_valid = serializers.ReadOnlyField()
    days_until_expiry = serializers.ReadOnlyField()
    policyholder_name = serializers.CharField(
        source='policyholder.full_name',
        read_only=True
    )
    vehicle_display = serializers.SerializerMethodField()
    total_premium = serializers.SerializerMethodField()

    class Meta:
        model = Quote
        fields = [
            'id', 'quote_number', 'policyholder', 'policyholder_name',
            'vehicle', 'vehicle_display', 'policy_type', 'coverage_level', 'status',
            'currency',                          # ADDED
            'customer_age', 'customer_credit_score', 'customer_years_experience',
            'vehicle_manufacture_year',          # RENAMED from vehicle_year
            'vehicle_make', 'vehicle_model', 'vehicle_value',
            'vehicle_has_anti_theft', 'vehicle_is_modified',
            'coverage_amount', 'deductible', 'base_premium', 'risk_adjustment',
            'discount_amount', 'final_premium', 'ml_predicted_premium',
            'confidence_score', 'risk_factors', 'has_roadside_assistance',
            'has_rental_coverage', 'has_glass_coverage', 'valid_until',
            'converted_policy', 'notes', 'customer_email', 'customer_phone',
            'is_valid', 'days_until_expiry', 'total_premium',
            'created_at', 'updated_at', 'sent_at'
        ]
        read_only_fields = [
            'id', 'quote_number', 'created_at', 'updated_at',
            'is_valid', 'days_until_expiry', 'ml_predicted_premium',
            'confidence_score', 'risk_factors'
        ]

    def get_vehicle_display(self, obj):
        """Return vehicle display string"""
        if obj.vehicle:
            # UPDATED: vehicle.year → vehicle.manufacture_year
            return f"{obj.vehicle.manufacture_year} {obj.vehicle.make} {obj.vehicle.model}"
        elif obj.vehicle_manufacture_year and obj.vehicle_make and obj.vehicle_model:
            # UPDATED: vehicle_year → vehicle_manufacture_year
            return f"{obj.vehicle_manufacture_year} {obj.vehicle_make} {obj.vehicle_model}"
        return None

    def get_total_premium(self, obj):
        """Calculate and return total premium"""
        return float(obj.calculate_total_premium())

    def validate(self, data):
        """Validate quote data"""
        # Ensure either policyholder or customer info is provided
        if not data.get('policyholder'):
            required_fields = ['customer_age', 'customer_credit_score', 'customer_years_experience']
            for field in required_fields:
                if not data.get(field):
                    raise serializers.ValidationError({
                        field: f'{field} is required for new customers'
                    })

        # Ensure either vehicle or vehicle info is provided
        if not data.get('vehicle'):
            # UPDATED: vehicle_year → vehicle_manufacture_year
            required_vehicle_fields = [
                'vehicle_manufacture_year', 'vehicle_make', 'vehicle_model', 'vehicle_value'
            ]
            for field in required_vehicle_fields:
                if not data.get(field):
                    raise serializers.ValidationError({
                        field: f'{field} is required for new vehicles'
                    })

        # Validate coverage amount vs deductible
        if data.get('coverage_amount') and data.get('deductible'):
            if data['deductible'] >= data['coverage_amount']:
                raise serializers.ValidationError({
                    'deductible': 'Deductible must be less than coverage amount'
                })

        return data

    def create(self, validated_data):
        """Generate quote number on creation"""
        if not validated_data.get('quote_number'):
            import random
            quote_num = f"QTE-{random.randint(100000000000, 999999999999)}"
            validated_data['quote_number'] = quote_num

        # Set valid_until to 30 days from now if not provided
        if not validated_data.get('valid_until'):
            validated_data['valid_until'] = date.today() + timedelta(days=30)

        return super().create(validated_data)


class QuoteListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing quotes"""

    policyholder_name = serializers.CharField(
        source='policyholder.full_name',
        read_only=True
    )
    vehicle_display = serializers.SerializerMethodField()
    is_valid = serializers.ReadOnlyField()

    class Meta:
        model = Quote
        fields = [
            'id', 'quote_number', 'policyholder_name', 'vehicle_display',
            'policy_type', 'coverage_level', 'status', 'final_premium',
            'valid_until', 'is_valid', 'created_at'
        ]

    def get_vehicle_display(self, obj):
        if obj.vehicle:
            return f"{obj.vehicle.make} {obj.vehicle.model}"
        elif obj.vehicle_make and obj.vehicle_model:
            return f"{obj.vehicle_make} {obj.vehicle_model}"
        return None


class QuoteCalculationInputSerializer(serializers.Serializer):
    """Serializer for quote calculation input"""

    # Policy details
    policy_type = serializers.ChoiceField(
        choices=['COMPREHENSIVE', 'THIRD_PARTY', 'COLLISION', 'LIABILITY']
    )
    coverage_level = serializers.ChoiceField(
        choices=['BASIC', 'STANDARD', 'PREMIUM']
    )
    coverage_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    deductible = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.00')
    )

    # Customer information (for new customers)
    policyholder_id = serializers.UUIDField(required=False, allow_null=True)
    customer_age = serializers.IntegerField(
        min_value=18,
        max_value=100,
        required=False,
        allow_null=True
    )
    customer_credit_score = serializers.IntegerField(
        min_value=300,
        max_value=850,
        required=False,
        allow_null=True
    )
    customer_years_experience = serializers.IntegerField(
        min_value=0,
        required=False,
        default=0
    )

    # Vehicle information (for new vehicles)
    vehicle_id = serializers.UUIDField(required=False, allow_null=True)
    # RENAMED: vehicle_year → vehicle_manufacture_year
    vehicle_manufacture_year = serializers.IntegerField(
        min_value=1900,
        max_value=2030,
        required=False,
        allow_null=True
    )
    vehicle_make = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True
    )
    vehicle_model = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True
    )
    vehicle_value = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.00'),
        required=False,
        allow_null=True
    )
    vehicle_has_anti_theft = serializers.BooleanField(default=False)
    vehicle_is_modified = serializers.BooleanField(default=False)

    # Optional coverages
    has_roadside_assistance = serializers.BooleanField(default=False)
    has_rental_coverage = serializers.BooleanField(default=False)
    has_glass_coverage = serializers.BooleanField(default=False)
    
    def validate_coverage_amount(self, value):
        """Validate against dynamic minimum from settings"""
        from system_settings.models import GlobalPricingSettings
        settings = GlobalPricingSettings.get_solo()
        
        if value < settings.minimum_coverage_amount:
            raise serializers.ValidationError(
                f'Coverage amount must be at least {settings.minimum_coverage_amount}.'
            )
        return value


    def validate(self, data):
        """Validate that either IDs or details are provided"""
        # Check customer info
        if not data.get('policyholder_id'):
            if not all([
                data.get('customer_age'),
                data.get('customer_credit_score')
            ]):
                raise serializers.ValidationError(
                    "Either policyholder_id or customer details (age, credit_score) must be provided"
                )

        # Check vehicle info
        if not data.get('vehicle_id'):
            # UPDATED: vehicle_year → vehicle_manufacture_year
            if not all([
                data.get('vehicle_manufacture_year'),
                data.get('vehicle_make'),
                data.get('vehicle_model'),
                data.get('vehicle_value')
            ]):
                raise serializers.ValidationError(
                    "Either vehicle_id or vehicle details (manufacture_year, make, model, value) must be provided"
                )

        # Validate deductible vs coverage
        if data['deductible'] >= data['coverage_amount']:
            raise serializers.ValidationError(
                "Deductible must be less than coverage amount"
            )

        return data


class PriceHistorySerializer(serializers.ModelSerializer):
    """Serializer for PriceHistory model"""

    is_current = serializers.ReadOnlyField()
    policy_number = serializers.CharField(
        source='policy.policy_number',
        read_only=True
    )
    policyholder_name = serializers.CharField(
        source='policy.policyholder.full_name',
        read_only=True
    )

    class Meta:
        model = PriceHistory
        fields = [
            'id', 'policy', 'policy_number', 'policyholder_name', 'quote',
            'previous_premium', 'new_premium', 'premium_change',
            'premium_change_percentage', 'change_reason', 'change_description',
            'risk_score_snapshot', 'risk_factors_snapshot', 'effective_from',
            'effective_to', 'is_current', 'created_by', 'notes', 'created_at'
        ]
        read_only_fields = [
            'id', 'premium_change', 'premium_change_percentage',
            'is_current', 'created_at'
        ]

    def validate(self, data):
        """Validate price history dates"""
        if data.get('effective_from') and data.get('effective_to'):
            if data['effective_from'] >= data['effective_to']:
                raise serializers.ValidationError({
                    'effective_to': 'Effective to date must be after effective from date'
                })
        return data


class PriceHistoryListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing price history"""

    policy_number = serializers.CharField(
        source='policy.policy_number',
        read_only=True
    )
    is_current = serializers.ReadOnlyField()

    class Meta:
        model = PriceHistory
        fields = [
            'id', 'policy_number', 'previous_premium', 'new_premium',
            'premium_change', 'premium_change_percentage', 'change_reason',
            'effective_from', 'effective_to', 'is_current', 'created_at'
        ]


class PriceComparisonSerializer(serializers.Serializer):
    """Serializer for price comparison results"""

    quote_number = serializers.CharField()
    policy_type = serializers.CharField()
    coverage_level = serializers.CharField()
    base_premium = serializers.DecimalField(max_digits=10, decimal_places=2)
    risk_adjustment = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    final_premium = serializers.DecimalField(max_digits=10, decimal_places=2)
    risk_factors = serializers.JSONField()
    savings_vs_standard = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False
    )