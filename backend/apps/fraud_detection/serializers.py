"""
Django REST Framework Serializers for Fraud Detection models
"""

from rest_framework import serializers
from .models import Policyholder, Vehicle, Policy, Claim
from datetime import date


class PolicyholderSerializer(serializers.ModelSerializer):
    """Serializer for Policyholder model"""
    
    full_name = serializers.ReadOnlyField()
    age = serializers.ReadOnlyField()
    
    class Meta:
        model = Policyholder
        fields = [
            'id', 'policy_holder_id', 'first_name', 'last_name', 'full_name',
            'date_of_birth', 'age', 'gender', 'email', 'phone_number',
            'address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country',
            'marital_status', 'occupation', 'annual_income', 'credit_score',
            'years_with_company', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'full_name', 'age']
    
    def validate_date_of_birth(self, value):
        """Validate that policyholder is at least 18 years old"""
        today = date.today()
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        if age < 18:
            raise serializers.ValidationError("Policyholder must be at least 18 years old.")
        if age > 100:
            raise serializers.ValidationError("Please verify the date of birth.")
        return value
    
    def validate_credit_score(self, value):
        """Validate credit score range"""
        if not (300 <= value <= 850):
            raise serializers.ValidationError("Credit score must be between 300 and 850.")
        return value


class PolicyholderListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing policyholders"""
    
    full_name = serializers.ReadOnlyField()
    age = serializers.ReadOnlyField()
    
    class Meta:
        model = Policyholder
        fields = [
            'id', 'policy_holder_id', 'full_name', 'age', 'email',
            'phone_number', 'city', 'state', 'is_active', 'created_at'
        ]


class VehicleSerializer(serializers.ModelSerializer):
    """Serializer for Vehicle model"""
    
    vehicle_age = serializers.ReadOnlyField()
    policyholder_name = serializers.CharField(source='policyholder.full_name', read_only=True)
    
    class Meta:
        model = Vehicle
        fields = [
            'id', 'vehicle_id', 'make', 'model', 'year', 'vehicle_age', 'vehicle_type',
            'vin', 'registration_number', 'engine_capacity', 'fuel_type', 'seating_capacity',
            'market_value', 'odometer_reading', 'has_anti_theft', 'has_airbags',
            'has_abs', 'is_modified', 'policyholder', 'policyholder_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'vehicle_age']
    
    def validate_year(self, value):
        """Validate vehicle year"""
        current_year = date.today().year
        if value < 1900 or value > current_year + 1:
            raise serializers.ValidationError(
                f"Vehicle year must be between 1900 and {current_year + 1}."
            )
        return value
    
    def validate_vin(self, value):
        """Validate VIN format"""
        if len(value) != 17:
            raise serializers.ValidationError("VIN must be exactly 17 characters.")
        if any(char in value.upper() for char in ['I', 'O', 'Q']):
            raise serializers.ValidationError("VIN cannot contain I, O, or Q.")
        return value.upper()


class VehicleListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing vehicles"""
    
    policyholder_name = serializers.CharField(source='policyholder.full_name', read_only=True)
    
    class Meta:
        model = Vehicle
        fields = [
            'id', 'vehicle_id', 'make', 'model', 'year', 'vehicle_type',
            'registration_number', 'market_value', 'policyholder_name', 'created_at'
        ]


class PolicySerializer(serializers.ModelSerializer):
    """Serializer for Policy model"""
    
    is_active = serializers.ReadOnlyField()
    days_until_expiry = serializers.ReadOnlyField()
    policyholder_name = serializers.CharField(source='policyholder.full_name', read_only=True)
    vehicle_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Policy
        fields = [
            'id', 'policy_number', 'policyholder', 'policyholder_name',
            'vehicle', 'vehicle_display', 'policy_type', 'coverage_level', 'status',
            'premium_amount', 'coverage_amount', 'deductible', 'start_date', 'end_date',
            'has_roadside_assistance', 'has_rental_coverage', 'has_glass_coverage',
            'is_active', 'days_until_expiry', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_active', 'days_until_expiry']
    
    def get_vehicle_display(self, obj):
        """Return vehicle display string"""
        return f"{obj.vehicle.year} {obj.vehicle.make} {obj.vehicle.model}"
    
    def validate(self, data):
        """Validate policy dates"""
        if 'start_date' in data and 'end_date' in data:
            if data['start_date'] >= data['end_date']:
                raise serializers.ValidationError({
                    'end_date': 'End date must be after start date.'
                })
        return data
    
    def validate_premium_amount(self, value):
        """Validate premium amount"""
        if value <= 0:
            raise serializers.ValidationError("Premium amount must be greater than zero.")
        return value


class PolicyListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing policies"""
    
    policyholder_name = serializers.CharField(source='policyholder.full_name', read_only=True)
    vehicle_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Policy
        fields = [
            'id', 'policy_number', 'policyholder_name', 'vehicle_display',
            'policy_type', 'status', 'premium_amount', 'start_date', 'end_date'
        ]
    
    def get_vehicle_display(self, obj):
        return f"{obj.vehicle.make} {obj.vehicle.model}"


class ClaimSerializer(serializers.ModelSerializer):
    """Serializer for Claim model"""
    
    days_since_submission = serializers.ReadOnlyField()
    processing_time = serializers.ReadOnlyField()
    policyholder_name = serializers.CharField(source='policyholder.full_name', read_only=True)
    policy_number = serializers.CharField(source='policy.policy_number', read_only=True)
    vehicle_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Claim
        fields = [
            'id', 'claim_number', 'policy', 'policy_number', 'policyholder',
            'policyholder_name', 'vehicle', 'vehicle_display', 'claim_type',
            'claim_status', 'severity', 'incident_date', 'incident_location',
            'incident_description', 'police_report_filed', 'police_report_number',
            'witnesses_present', 'number_of_witnesses', 'number_of_vehicles_involved',
            'number_of_injuries', 'third_party_involved', 'claimed_amount',
            'approved_amount', 'paid_amount', 'fraud_score', 'is_fraudulent',
            'fraud_reason', 'submitted_date', 'reviewed_date', 'closed_date',
            'days_since_submission', 'processing_time', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'submitted_date', 'created_at', 'updated_at',
            'days_since_submission', 'processing_time'
        ]
    
    def get_vehicle_display(self, obj):
        """Return vehicle display string"""
        return f"{obj.vehicle.year} {obj.vehicle.make} {obj.vehicle.model}"
    
    def validate(self, data):
        """Validate claim data"""
        if 'claimed_amount' in data and 'policy' in data:
            if data['claimed_amount'] > data['policy'].coverage_amount:
                raise serializers.ValidationError({
                    'claimed_amount': 'Claimed amount cannot exceed policy coverage amount.'
                })
        
        if 'incident_date' in data:
            if data['incident_date'] > date.today():
                raise serializers.ValidationError({
                    'incident_date': 'Incident date cannot be in the future.'
                })
        
        return data


class ClaimListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing claims"""
    
    policyholder_name = serializers.CharField(source='policyholder.full_name', read_only=True)
    policy_number = serializers.CharField(source='policy.policy_number', read_only=True)
    
    class Meta:
        model = Claim
        fields = [
            'id', 'claim_number', 'policy_number', 'policyholder_name',
            'claim_type', 'claim_status', 'severity', 'claimed_amount',
            'fraud_score', 'is_fraudulent', 'incident_date', 'submitted_date'
        ]


class ClaimFraudAnalysisSerializer(serializers.ModelSerializer):
    """Serializer for fraud analysis results"""
    
    class Meta:
        model = Claim
        fields = [
            'id', 'claim_number', 'fraud_score', 'is_fraudulent', 'fraud_reason'
        ]
        read_only_fields = fields