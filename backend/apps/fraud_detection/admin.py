"""
Django Admin configuration for Fraud Detection models
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Policyholder, Vehicle, Policy, Claim


@admin.register(Policyholder)
class PolicyholderAdmin(admin.ModelAdmin):
    list_display = [
        'policy_holder_id', 'full_name', 'email', 'age',
        'credit_score', 'occupation', 'is_active', 'created_at'
    ]
    list_filter = ['is_active', 'gender', 'marital_status', 'occupation', 'created_at']
    search_fields = ['policy_holder_id', 'first_name', 'last_name', 'email', 'phone_number']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Identification', {
            'fields': ('id', 'policy_holder_id', 'is_active')
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'date_of_birth', 'gender')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone_number')
        }),
        ('Address', {
            'fields': ('address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country')
        }),
        ('Demographics', {
            'fields': ('marital_status', 'occupation', 'annual_income', 'credit_score')
        }),
        ('Account History', {
            'fields': ('years_with_company', 'created_at', 'updated_at')
        }),
    )
    
    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = 'Name'
    
    def age(self, obj):
        return obj.age
    age.short_description = 'Age'


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = [
        'vehicle_id', 'vehicle_display', 'year', 'vehicle_type',
        'fuel_type', 'market_value', 'policyholder', 'created_at'
    ]
    list_filter = ['vehicle_type', 'fuel_type', 'year', 'has_anti_theft', 'is_modified']
    search_fields = ['vehicle_id', 'vin', 'registration_number', 'make', 'model']
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['policyholder']
    
    fieldsets = (
        ('Identification', {
            'fields': ('id', 'vehicle_id', 'vin', 'registration_number')
        }),
        ('Vehicle Details', {
            'fields': ('make', 'model', 'year', 'vehicle_type')
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
    
    def vehicle_display(self, obj):
        return f"{obj.make} {obj.model}"
    vehicle_display.short_description = 'Vehicle'


@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    list_display = [
        'policy_number', 'policyholder', 'vehicle', 'policy_type',
        'status_badge', 'premium_amount', 'start_date', 'end_date', 'is_active'
    ]
    list_filter = ['status', 'policy_type', 'coverage_level', 'start_date', 'end_date']
    search_fields = ['policy_number', 'policyholder__first_name', 'policyholder__last_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
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
            'fields': ('premium_amount', 'coverage_amount', 'deductible')
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
    status_badge.short_description = 'Status'


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = [
        'claim_number', 'policyholder', 'claim_type', 'status_badge',
        'claimed_amount', 'fraud_indicator', 'incident_date', 'submitted_date'
    ]
    list_filter = [
        'claim_status', 'claim_type', 'severity', 'is_fraudulent',
        'police_report_filed', 'third_party_involved', 'submitted_date'
    ]
    search_fields = [
        'claim_number', 'policyholder__first_name',
        'policyholder__last_name', 'incident_description'
    ]
    readonly_fields = ['id', 'submitted_date', 'created_at', 'updated_at']
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
                'incident_date', 'incident_location', 'incident_description'
            )
        }),
        ('Police & Witnesses', {
            'fields': (
                'police_report_filed', 'police_report_number',
                'witnesses_present', 'number_of_witnesses'
            )
        }),
        ('Parties Involved', {
            'fields': (
                'number_of_vehicles_involved', 'number_of_injuries',
                'third_party_involved'
            )
        }),
        ('Financial Details', {
            'fields': ('claimed_amount', 'approved_amount', 'paid_amount')
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
    status_badge.short_description = 'Status'
    
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
    fraud_indicator.short_description = 'Fraud Risk'