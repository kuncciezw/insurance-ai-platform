"""
Django Admin Configuration for Claims Automation
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import ClaimEstimate, ClaimProcessingLog


@admin.register(ClaimEstimate)
class ClaimEstimateAdmin(admin.ModelAdmin):
    """Admin interface for ClaimEstimate model"""
    
    list_display = [
        'estimate_number', 'claim_number_link', 'estimated_cost_display',
        'predicted_severity_badge', 'triage_priority_badge',
        'processing_recommendation', 'confidence_display', 'created_at'
    ]
    
    list_filter = [
        'predicted_severity', 'triage_priority', 'processing_recommendation',
        'model_version', 'created_at'
    ]
    
    search_fields = [
        'estimate_number', 'claim__claim_number',
        'claim__policyholder__first_name', 'claim__policyholder__last_name'
    ]
    
    readonly_fields = [
        'id', 'estimate_number', 'variance_percentage', 'is_within_tolerance',
        'needs_review', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'id', 'estimate_number', 'claim', 'created_at', 'updated_at'
            )
        }),
        ('ML Predictions', {
            'fields': (
                'estimated_cost', 'confidence_score',
                'confidence_lower_bound', 'confidence_upper_bound',
                'predicted_severity', 'severity_score'
            )
        }),
        ('Processing Recommendations', {
            'fields': (
                'processing_recommendation', 'triage_priority',
                'estimated_processing_days', 'recommended_reserve',
                'reserve_adequacy_ratio'
            )
        }),
        ('Cost Breakdown', {
            'fields': ('cost_breakdown', 'risk_factors'),
            'classes': ('collapse',)
        }),
        ('Validation', {
            'fields': (
                'actual_settlement_amount', 'prediction_accuracy',
                'variance_percentage', 'is_within_tolerance', 'reviewed_at'
            ),
            'classes': ('collapse',)
        }),
        ('Manual Adjustments', {
            'fields': (
                'manual_adjustment', 'adjustment_reason',
                'adjusted_by', 'final_estimate'
            ),
            'classes': ('collapse',)
        }),
        ('Model Information', {
            'fields': ('model_version', 'features_used'),
            'classes': ('collapse',)
        }),
    )
    
    def claim_number_link(self, obj):
        """Display claim number as link"""
        return format_html(
            '<a href="/admin/fraud_detection/claim/{}/change/">{}</a>',
            obj.claim.id,
            obj.claim.claim_number
        )
    claim_number_link.short_description = 'Claim Number'
    
    def estimated_cost_display(self, obj):
        """Display estimated cost with formatting"""
        return format_html(
            '<strong>${:,.2f}</strong>',
            obj.estimated_cost
        )
    estimated_cost_display.short_description = 'Estimated Cost'
    estimated_cost_display.admin_order_field = 'estimated_cost'
    
    def predicted_severity_badge(self, obj):
        """Display severity with color badge"""
        colors = {
            'MINOR': '#28a745',
            'MODERATE': '#ffc107',
            'MAJOR': '#fd7e14',
            'CRITICAL': '#dc3545'
        }
        color = colors.get(obj.predicted_severity, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.predicted_severity
        )
    predicted_severity_badge.short_description = 'Severity'
    predicted_severity_badge.admin_order_field = 'predicted_severity'
    
    def triage_priority_badge(self, obj):
        """Display priority with color badge"""
        colors = {
            'LOW': '#28a745',
            'MEDIUM': '#17a2b8',
            'HIGH': '#fd7e14',
            'URGENT': '#dc3545'
        }
        color = colors.get(obj.triage_priority, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.triage_priority
        )
    triage_priority_badge.short_description = 'Priority'
    triage_priority_badge.admin_order_field = 'triage_priority'
    
    def confidence_display(self, obj):
        """Display confidence score with percentage"""
        percentage = obj.confidence_score * 100
        color = '#28a745' if percentage >= 80 else '#ffc107' if percentage >= 60 else '#dc3545'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color,
            percentage
        )
    confidence_display.short_description = 'Confidence'
    confidence_display.admin_order_field = 'confidence_score'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('claim', 'claim__policyholder')


@admin.register(ClaimProcessingLog)
class ClaimProcessingLogAdmin(admin.ModelAdmin):
    """Admin interface for ClaimProcessingLog model"""
    
    list_display = [
        'created_at', 'claim_number_link', 'action_type_badge',
        'is_automated_icon', 'performed_by', 'processing_time_display'
    ]
    
    list_filter = [
        'action_type', 'is_automated', 'performed_by', 'created_at'
    ]
    
    search_fields = [
        'claim__claim_number', 'action_description',
        'performed_by'
    ]
    
    readonly_fields = [
        'id', 'claim', 'estimate', 'action_type', 'action_description',
        'is_automated', 'performed_by', 'result_data', 'previous_value',
        'new_value', 'processing_time_ms', 'model_version', 'created_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'id', 'claim', 'estimate', 'created_at'
            )
        }),
        ('Action Details', {
            'fields': (
                'action_type', 'action_description',
                'is_automated', 'performed_by'
            )
        }),
        ('Results', {
            'fields': (
                'result_data', 'previous_value', 'new_value'
            )
        }),
        ('Performance', {
            'fields': (
                'processing_time_ms', 'model_version'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Disable manual creation of logs"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Disable deletion of logs"""
        return False
    
    def claim_number_link(self, obj):
        """Display claim number as link"""
        return format_html(
            '<a href="/admin/fraud_detection/claim/{}/change/">{}</a>',
            obj.claim.id,
            obj.claim.claim_number
        )
    claim_number_link.short_description = 'Claim Number'
    
    def action_type_badge(self, obj):
        """Display action type with badge"""
        colors = {
            'ESTIMATE_GENERATED': '#007bff',
            'TRIAGE_ASSIGNED': '#17a2b8',
            'RECOMMENDATION_MADE': '#28a745',
            'RESERVE_CALCULATED': '#ffc107',
            'MANUAL_REVIEW_TRIGGERED': '#fd7e14',
            'AUTO_APPROVED': '#28a745',
            'FRAUD_FLAG_RAISED': '#dc3545',
            'ESTIMATE_UPDATED': '#6c757d',
            'COST_RECALCULATED': '#6610f2'
        }
        color = colors.get(obj.action_type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.action_type.replace('_', ' ')
        )
    action_type_badge.short_description = 'Action'
    action_type_badge.admin_order_field = 'action_type'
    
    def is_automated_icon(self, obj):
        """Display automated status with icon"""
        if obj.is_automated:
            return format_html(
                '<span style="color: #28a745; font-size: 16px;" title="Automated">🤖</span>'
            )
        return format_html(
            '<span style="color: #007bff; font-size: 16px;" title="Manual">👤</span>'
        )
    is_automated_icon.short_description = 'Type'
    is_automated_icon.admin_order_field = 'is_automated'
    
    def processing_time_display(self, obj):
        """Display processing time"""
        if obj.processing_time_ms:
            if obj.processing_time_ms < 1000:
                return format_html(
                    '<span style="color: #28a745;">{} ms</span>',
                    obj.processing_time_ms
                )
            else:
                return format_html(
                    '<span style="color: #ffc107;">{:.2f} s</span>',
                    obj.processing_time_ms / 1000
                )
        return '-'
    processing_time_display.short_description = 'Processing Time'
    processing_time_display.admin_order_field = 'processing_time_ms'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('claim', 'estimate')