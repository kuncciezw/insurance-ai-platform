"""
Django Admin Configuration for Dynamic Pricing
Updated for Pipeline Architecture
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Quote, PriceHistory


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    """Admin interface for Quote model"""
    
    list_display = [
        'quote_number', 'policyholder_display', 'vehicle_display',
        'policy_type', 'coverage_level', 'currency', 'final_premium_display',
        'status', 'is_valid_display', 'created_at'
    ]
    list_filter = [
        'status', 'policy_type', 'coverage_level', 'currency',
        'has_roadside_assistance', 'has_rental_coverage',
        'has_glass_coverage', 'created_at'
    ]
    search_fields = [
        'quote_number', 'policyholder__first_name',
        'policyholder__last_name', 'customer_email',
        'vehicle__make', 'vehicle__model'
    ]
    readonly_fields = [
        'id', 'quote_number', 'ml_predicted_premium',
        'confidence_score', 'risk_factors', 'is_valid',
        'days_until_expiry', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Quote Information', {
            'fields': ('id', 'quote_number', 'status', 'valid_until')
        }),
        ('Customer Information', {
            'fields': (
                'policyholder', 'customer_age', 'customer_credit_score',
                'customer_years_experience', 'customer_email', 'customer_phone'
            )
        }),
        ('Vehicle Information', {
            # REMOVED vehicle_year, ADDED vehicle_manufacture_year
            'fields': (
                'vehicle', 'vehicle_manufacture_year', 'vehicle_make', 'vehicle_model',
                'vehicle_value', 'vehicle_has_anti_theft', 'vehicle_is_modified'
            )
        }),
        ('Policy Details', {
            # ADDED currency
            'fields': (
                'policy_type', 'coverage_level', 'currency', 'coverage_amount', 'deductible'
            )
        }),
        ('Pricing', {
            'fields': (
                'base_premium', 'risk_adjustment', 'discount_amount',
                'final_premium', 'ml_predicted_premium', 'confidence_score',
                'risk_factors'
            )
        }),
        ('Optional Coverages', {
            'fields': (
                'has_roadside_assistance', 'has_rental_coverage',
                'has_glass_coverage'
            )
        }),
        ('Conversion', {
            'fields': ('converted_policy', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'sent_at')
        }),
    )
    
    @admin.display(description='Policyholder')
    def policyholder_display(self, obj):
        """Display policyholder name"""
        if obj.policyholder:
            return obj.policyholder.full_name
        return "New Customer"
    
    @admin.display(description='Vehicle')
    def vehicle_display(self, obj):
        """Display vehicle information"""
        if obj.vehicle:
            # Changed year to manufacture_year
            return f"{obj.vehicle.manufacture_year} {obj.vehicle.make} {obj.vehicle.model}"
        elif obj.vehicle_manufacture_year and obj.vehicle_make and obj.vehicle_model:
            return f"{obj.vehicle_manufacture_year} {obj.vehicle_make} {obj.vehicle_model}"
        return "N/A"
    
    @admin.display(description='Final Premium')
    def final_premium_display(self, obj):
        """Display final premium with color coding"""
        color = 'green' if obj.final_premium < 1000 else 'orange' if obj.final_premium < 2000 else 'red'
        return format_html(
            '<span style="color: {};">${:,.2f}</span>',
            color,
            obj.final_premium
        )
    
    @admin.display(description='Valid')
    def is_valid_display(self, obj):
        """Display validity status"""
        if obj.is_valid:
            return format_html('<span style="color: green;">✓ Valid</span>')
        return format_html('<span style="color: red;">✗ Expired</span>')
    
    actions = ['mark_as_sent', 'mark_as_expired']
    
    @admin.action(description='Mark selected quotes as sent')
    def mark_as_sent(self, request, queryset):
        """Mark selected quotes as sent"""
        from django.utils import timezone
        updated = queryset.filter(status='CALCULATED').update(
            status='SENT',
            sent_at=timezone.now()
        )
        self.message_user(request, f'{updated} quotes marked as sent.')
    
    @admin.action(description='Mark selected quotes as expired')
    def mark_as_expired(self, request, queryset):
        """Mark selected quotes as expired"""
        updated = queryset.update(status='EXPIRED')
        self.message_user(request, f'{updated} quotes marked as expired.')


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    """Admin interface for PriceHistory model"""
    
    list_display = [
        'policy_number_display', 'policyholder_display',
        'previous_premium_display', 'new_premium_display',
        'change_display', 'change_reason', 'effective_from',
        'is_current_display', 'created_at'
    ]
    list_filter = [
        'change_reason', 'effective_from', 'created_at'
    ]
    search_fields = [
        'policy__policy_number', 'policy__policyholder__first_name',
        'policy__policyholder__last_name'
    ]
    readonly_fields = [
        'id', 'premium_change', 'premium_change_percentage',
        'is_current', 'created_at'
    ]
    
    fieldsets = (
        ('Policy Information', {
            'fields': ('policy', 'quote')
        }),
        ('Price Change', {
            'fields': (
                'previous_premium', 'new_premium', 'premium_change',
                'premium_change_percentage'
            )
        }),
        ('Change Details', {
            'fields': (
                'change_reason', 'change_description', 'risk_score_snapshot',
                'risk_factors_snapshot'
            )
        }),
        ('Effective Dates', {
            'fields': ('effective_from', 'effective_to')
        }),
        ('Metadata', {
            'fields': ('created_by', 'notes', 'created_at')
        }),
    )
    
    @admin.display(description='Policy Number')
    def policy_number_display(self, obj):
        """Display policy number"""
        return obj.policy.policy_number
    
    @admin.display(description='Policyholder')
    def policyholder_display(self, obj):
        """Display policyholder name"""
        return obj.policy.policyholder.full_name
    
    @admin.display(description='Previous Premium')
    def previous_premium_display(self, obj):
        """Display previous premium"""
        if obj.previous_premium:
            return f"${obj.previous_premium:,.2f}"
        return "N/A"
    
    @admin.display(description='New Premium')
    def new_premium_display(self, obj):
        """Display new premium"""
        return f"${obj.new_premium:,.2f}"
    
    @admin.display(description='Change')
    def change_display(self, obj):
        """Display premium change with color coding"""
        if obj.premium_change > 0:
            color = 'red'
            symbol = '▲'
        elif obj.premium_change < 0:
            color = 'green'
            symbol = '▼'
        else:
            color = 'gray'
            symbol = '='
        
        return format_html(
            '<span style="color: {};">{} ${:,.2f} ({:.1f}%)</span>',
            color,
            symbol,
            abs(obj.premium_change),
            abs(obj.premium_change_percentage)
        )
    
    @admin.display(description='Current')
    def is_current_display(self, obj):
        """Display current status"""
        if obj.is_current:
            return format_html('<span style="color: green;">✓ Current</span>')
        return format_html('<span style="color: gray;">○ Historical</span>')