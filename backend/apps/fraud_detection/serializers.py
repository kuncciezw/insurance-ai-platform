"""
Django REST Framework Serializers for Fraud Detection models
Updated for Pipeline Architecture
"""

from rest_framework import serializers
from .models import Policyholder, Vehicle, Policy, Claim
from datetime import date, timedelta

class PolicyholderSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    age = serializers.ReadOnlyField()
    annual_income = serializers.ReadOnlyField()
    
    class Meta:
        model = Policyholder
        fields = [
            'id', 'policy_holder_id', 'first_name', 'last_name', 'full_name',
            'date_of_birth', 'age', 'gender', 'national_id', 'email', 'phone_number',
            'address_line1', 'address_line2', 'city', 'state', 'country',
            'marital_status', 'occupation', 'monthly_income', 'annual_income', 
            'has_driving_license', 'has_defensive_license', 'is_medical_license_valid',
            'credit_score', 'credit_rating', 'years_with_company', 'is_active', 
            'created_at', 'updated_at'
        ]
        # Credit score & rating are auto-calculated now, so they are read-only
        read_only_fields = ['id', 'created_at', 'updated_at', 'full_name', 'age', 'annual_income', 'credit_score', 'credit_rating']
    
    def validate_date_of_birth(self, value):
        today = date.today()
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        if age < 18:
            raise serializers.ValidationError("Policyholder must be at least 18 years old.")
        return value

class PolicyholderListSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    age = serializers.ReadOnlyField()
    
    class Meta:
        model = Policyholder
        fields = [
            'id', 'policy_holder_id', 'full_name', 'age', 'email',
            'phone_number', 'city', 'state', 'is_active', 'credit_rating'
        ]

class VehicleSerializer(serializers.ModelSerializer):
    vehicle_age = serializers.ReadOnlyField()
    policyholder_name = serializers.CharField(source='policyholder.full_name', read_only=True)
    
    class Meta:
        model = Vehicle
        fields = [
            'id', 'make', 'model', 'manufacture_year', 'vehicle_age', 'vehicle_type',
            'vin', 'registration_number', 'engine_capacity', 'fuel_type', 'seating_capacity',
            'market_value', 'odometer_reading', 'has_anti_theft', 'has_airbags',
            'has_abs', 'is_modified', 'policyholder', 'policyholder_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'vehicle_age']
    
    def validate_manufacture_year(self, value):
        current_year = date.today().year
        if value < 1900 or value > current_year + 1:
            raise serializers.ValidationError(f"Vehicle year must be between 1900 and {current_year + 1}.")
        return value

class VehicleListSerializer(serializers.ModelSerializer):
    policyholder_name = serializers.CharField(source='policyholder.full_name', read_only=True)
    
    class Meta:
        model = Vehicle
        fields = [
            'id', 'make', 'model', 'manufacture_year', 'vehicle_type',
            'registration_number', 'market_value', 'policyholder_name',
            'policyholder'
        ]

class PolicySerializer(serializers.ModelSerializer):
    is_active = serializers.ReadOnlyField()
    days_until_expiry = serializers.ReadOnlyField()
    policyholder_name = serializers.CharField(source='policyholder.full_name', read_only=True)
    vehicle_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Policy
        fields = [
            'id', 'policy_number', 'policyholder', 'policyholder_name',
            'vehicle', 'vehicle_display', 'policy_type', 'coverage_level', 'status', 'currency',
            'premium_amount', 'coverage_amount', 'deductible', 'start_date', 'end_date',
            'has_roadside_assistance', 'has_rental_coverage', 'has_glass_coverage',
            'is_active', 'days_until_expiry', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_active', 'days_until_expiry', 'premium_amount', 'coverage_amount', 'deductible']
    
    def get_vehicle_display(self, obj):
        return f"{obj.vehicle.manufacture_year} {obj.vehicle.make} {obj.vehicle.model}"
    
    def validate(self, data):
        """Set start_date to today if not provided"""
        if 'start_date' not in data:
            data['start_date'] = date.today()
        
        # Auto-calculate end_date if not provided (1 year from start)
        if 'end_date' not in data and 'start_date' in data:
            data['end_date'] = data['start_date'] + timedelta(days=365)
        
        return data

class PolicyListSerializer(serializers.ModelSerializer):
    policyholder_name = serializers.CharField(source='policyholder.full_name', read_only=True)
    vehicle_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Policy
        fields = [
            'id', 'policy_number', 'policyholder', 'policyholder_name',
            'vehicle', 'vehicle_display', 'policy_type', 'status',      
            'currency', 'premium_amount', 'start_date', 'end_date'
        ]
    
    def get_vehicle_display(self, obj):
        return f"{obj.vehicle.make} {obj.vehicle.model}"

class ClaimSerializer(serializers.ModelSerializer):
    days_since_submission = serializers.ReadOnlyField()
    policyholder_name = serializers.CharField(source='policyholder.full_name', read_only=True)
    policy_number = serializers.CharField(source='policy.policy_number', read_only=True)
    vehicle_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Claim
        fields = [
            'id', 'claim_number', 'policy', 'policy_number', 'policyholder',
            'policyholder_name', 'vehicle', 'vehicle_display', 'claim_type',
            'claim_status', 'severity', 'incident_date', 'incident_location',
            'incident_evidence', 'number_of_vehicles_involved', 
            'payment_method', 'claimed_amount', 'approved_amount', 'paid_amount', 
            'fraud_score', 'is_fraudulent', 'fraud_reason', 'submitted_date', 
            'reviewed_date', 'closed_date', 'days_since_submission', 'created_at', 'updated_at'
        ]
        # Claim statuses and amounts are managed by the ML estimator and system backend now
        read_only_fields = [
            'id', 'submitted_date', 'created_at', 'updated_at', 'days_since_submission',
            'claim_status', 'approved_amount', 'paid_amount', 'fraud_score', 'is_fraudulent',
            'policyholder', 'vehicle'  # These are auto-populated from policy
        ]
    
    def get_vehicle_display(self, obj):
        return f"{obj.vehicle.manufacture_year} {obj.vehicle.make} {obj.vehicle.model}"
    
    def validate(self, data):
        """Auto-populate policyholder and vehicle from policy"""
        if 'policy' in data:
            data['policyholder'] = data['policy'].policyholder
            data['vehicle'] = data['policy'].vehicle
        return data

class ClaimListSerializer(serializers.ModelSerializer):
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
    class Meta:
        model = Claim
        fields = ['id', 'claim_number', 'fraud_score', 'is_fraudulent', 'fraud_reason']