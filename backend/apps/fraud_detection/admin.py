"""
Django Admin configuration for Fraud Detection models
Updated for the New Pipeline Architecture
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Policyholder, Vehicle, Policy, Claim


@admin.register(Policyholder)
class PolicyholderAdmin(admin.ModelAdmin):
    list_display = [
        'policy_holder_id', 'full_name', 'email', 'age',
        'credit_score', 'credit_rating', 'occupation', 'is_active', 'created_at'
    ]
    list_filter = ['is_active', 'gender', 'marital_status', 'occupation', 'credit_rating']
    search_fields = ['policy_holder_id', 'first_name', 'last_name', 'email', 'phone_number']
    readonly_fields = ['id', 'created_at', 'updated_at', 'credit_score', 'credit_rating', 'annual_income']
    
    fieldsets = (
        ('Identification', {
            'fields': ('id', 'policy_holder_id', 'is_active')
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'date_of_birth', 'gender', 'national_id')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone_number')
        }),
        ('Address', {
            # REMOVED postal_code
            'fields': ('address_line1', 'address_line2', 'city', 'state', 'country')
        }),
        ('Demographics & Financials', {
            'fields': ('marital_status', 'occupation', 'monthly_income', 'annual_income')
        }),
        ('Risk & Licenses', {
            # ADDED new license fields and credit rating
            'fields': ('has_driving_license', 'has_defensive_license', 'is_medical_license_valid', 'credit_score', 'credit_rating')
        }),
        ('Account History', {
            'fields': ('years_with_company', 'created_at', 'updated_at')
        }),
    )
    
    @admin.display(description='Name')
    def full_name(self, obj):
        return obj.full_name
    
    @admin.display(description='Age')
    def age(self, obj):
        return obj.age


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = [
        'registration_number', 'vehicle_display', 'manufacture_year', 'vehicle_type',
        'fuel_type', 'market_value', 'policyholder', 'created_at'
    ]
    list_filter = ['vehicle_type', 'fuel_type', 'manufacture_year', 'has_anti_theft', 'is_modified']
    search_fields = ['vin', 'registration_number', 'make', 'model']
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['policyholder']
    
    fieldsets = (
        ('Identification', {
            'fields': ('id', 'vin', 'registration_number')
        }),
        ('Vehicle Details', {
            'fields': ('make', 'model', 'manufacture_year', 'vehicle_type')
        }),
        ('Technical Specifications', {
            'fields': ('engine_capacity', 'fuel_type', 'seating_capacity')
        }),
        ('Value & Condition', {
            'fields': ('market_value', 'odometer_reading')
        }),
        ('Safety Features', {
            'fields': ('has_anti_theft', 'has_airbags', 'has_abs', 'is_modified')
        }),
        ('Ownership', {
            'fields': ('policyholder',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    @admin.display(description='Vehicle')
    def vehicle_display(self, obj):
        return f"{obj.make} {obj.model}"


@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    list_display = [
        'policy_number', 'policyholder', 'vehicle', 'policy_type',
        'status_badge', 'currency', 'premium_amount', 'start_date', 'end_date', 'is_active'
    ]
    list_filter = ['status', 'policy_type', 'coverage_level', 'currency', 'start_date', 'end_date']
    search_fields = ['policy_number', 'policyholder__first_name', 'policyholder__last_name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'premium_amount', 'coverage_amount', 'deductible']
    raw_id_fields = ['policyholder', 'vehicle']
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Identification', {
            'fields': ('id', 'policy_number')
        }),
        ('Relationships', {
            'fields': ('policyholder', 'vehicle')
        }),
        ('Policy Details', {
            'fields': ('policy_type', 'coverage_level', 'status')
        }),
        ('Financial Information', {
            'fields': ('currency', 'premium_amount', 'coverage_amount', 'deductible')
        }),
        ('Coverage Period', {
            'fields': ('start_date', 'end_date')
        }),
        ('Additional Coverage', {
            'fields': ('has_roadside_assistance', 'has_rental_coverage', 'has_glass_coverage')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            'ACTIVE': 'green',
            'EXPIRED': 'red',
            'CANCELLED': 'orange',
            'SUSPENDED': 'gray',
            'PENDING': 'blue',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = [
        'claim_number', 'policyholder', 'claim_type', 'status_badge',
        'claimed_amount', 'payment_method', 'fraud_indicator', 'incident_date', 'submitted_date'
    ]
    list_filter = [
        'claim_status', 'claim_type', 'severity', 'is_fraudulent', 'payment_method', 'submitted_date'
    ]
    search_fields = [
        'claim_number', 'policyholder__first_name',
        'policyholder__last_name', 'incident_description'
    ]
    readonly_fields = ['id', 'submitted_date', 'created_at', 'updated_at', 'claimed_amount', 'approved_amount', 'paid_amount', 'fraud_score', 'is_fraudulent', 'claim_status']
    raw_id_fields = ['policy', 'policyholder', 'vehicle']
    date_hierarchy = 'incident_date'
    
    fieldsets = (
        ('Identification', {
            'fields': ('id', 'claim_number')
        }),
        ('Relationships', {
            'fields': ('policy', 'policyholder', 'vehicle')
        }),
        ('Claim Information', {
            'fields': ('claim_type', 'claim_status', 'severity')
        }),
        ('Incident Details', {
            'fields': (
                'incident_date', 'incident_location', 'incident_evidence', 'incident_description'
            )
        }),
        ('Parties Involved', {
            'fields': (
                'number_of_vehicles_involved',
            )
        }),
        ('Financial Details', {
            'fields': ('payment_method', 'claimed_amount', 'approved_amount', 'paid_amount')
        }),
        ('Fraud Detection', {
            'fields': ('fraud_score', 'is_fraudulent', 'fraud_reason'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'submitted_date', 'reviewed_date', 'closed_date',
                'created_at', 'updated_at'
            )
        }),
    )
    
    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            'SUBMITTED': 'blue',
            'UNDER_REVIEW': 'orange',
            'APPROVED': 'green',
            'REJECTED': 'red',
            'PAID': 'darkgreen',
            'CLOSED': 'gray',
        }
        color = colors.get(obj.claim_status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_claim_status_display()
        )
    
    @admin.display(description='Fraud Risk')
    def fraud_indicator(self, obj):
        if obj.is_fraudulent or obj.fraud_score > 0.7:
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠ {:.2%}</span>',
                obj.fraud_score
            )
        elif obj.fraud_score > 0.5:
            return format_html(
                '<span style="color: orange; font-weight: bold;">⚡ {:.2%}</span>',
                obj.fraud_score
            )
        else:
            return format_html(
                '<span style="color: green;">✓ {:.2%}</span>',
                obj.fraud_score
            )