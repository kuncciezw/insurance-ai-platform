"""
Models for Claims Automation Application
Includes ClaimEstimate and ClaimProcessingLog models
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid
from apps.fraud_detection.models import Claim, Policy


class ClaimEstimate(models.Model):
    """
    ML-based claim cost estimation model
    Stores automated cost predictions for claims
    """
    SEVERITY_CHOICES = [
        ('MINOR', 'Minor'),
        ('MODERATE', 'Moderate'),
        ('MAJOR', 'Major'),
        ('CRITICAL', 'Critical'),
    ]
    
    TRIAGE_PRIORITY_CHOICES = [
        ('LOW', 'Low Priority'),
        ('MEDIUM', 'Medium Priority'),
        ('HIGH', 'High Priority'),
        ('URGENT', 'Urgent'),
    ]
    
    RECOMMENDATION_CHOICES = [
        ('AUTO_APPROVE', 'Auto Approve'),
        ('MANUAL_REVIEW', 'Manual Review Required'),
        ('DETAILED_INVESTIGATION', 'Detailed Investigation'),
        ('REJECT', 'Recommend Rejection'),
    ]

    # Primary identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    estimate_number = models.CharField(max_length=20, unique=True, db_index=True)
    
    # Relationships
    claim = models.OneToOneField(
        Claim,
        on_delete=models.CASCADE,
        related_name='cost_estimate'
    )
    
    # ML Predictions
    estimated_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="ML predicted settlement cost"
    )
    confidence_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Model confidence in prediction (0-1)"
    )
    confidence_lower_bound = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Lower bound of confidence interval"
    )
    confidence_upper_bound = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Upper bound of confidence interval"
    )
    
    # Severity Assessment
    predicted_severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        help_text="ML predicted claim severity"
    )
    severity_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Severity score (0-1)"
    )
    
    # Reserve Recommendations
    recommended_reserve = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Recommended reserve amount"
    )
    reserve_adequacy_ratio = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.0)],
        help_text="Ratio of reserve to estimated cost"
    )
    
    # Processing Recommendations
    processing_recommendation = models.CharField(
        max_length=30,
        choices=RECOMMENDATION_CHOICES,
        default='MANUAL_REVIEW'
    )
    triage_priority = models.CharField(
        max_length=20,
        choices=TRIAGE_PRIORITY_CHOICES,
        default='MEDIUM'
    )
    estimated_processing_days = models.IntegerField(
        default=7,
        validators=[MinValueValidator(1)],
        help_text="Estimated days to process claim"
    )
    
    # Cost Breakdown (JSON for flexibility)
    cost_breakdown = models.JSONField(
        default=dict,
        blank=True,
        help_text="Detailed cost breakdown by category"
    )
    
    # Risk Factors
    risk_factors = models.JSONField(
        default=dict,
        blank=True,
        help_text="Factors contributing to cost estimate"
    )
    
    # Comparison with actual (if available)
    actual_settlement_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Actual settlement amount (for model validation)"
    )
    prediction_accuracy = models.FloatField(
        null=True,
        blank=True,
        help_text="Accuracy of prediction compared to actual"
    )
    
    # Model Information
    model_version = models.CharField(max_length=20, default='1.0')
    features_used = models.JSONField(
        default=list,
        blank=True,
        help_text="List of features used in prediction"
    )
    
    # Adjustments
    manual_adjustment = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Manual adjustment by claims adjuster"
    )
    adjustment_reason = models.TextField(blank=True, null=True)
    adjusted_by = models.CharField(max_length=100, blank=True, null=True)
    
    # Final estimate
    final_estimate = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Final estimate after adjustments"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'claim_estimates'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['estimate_number']),
            models.Index(fields=['claim']),
            models.Index(fields=['predicted_severity']),
            models.Index(fields=['triage_priority']),
            models.Index(fields=['processing_recommendation']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = 'Claim Estimate'
        verbose_name_plural = 'Claim Estimates'

    def __str__(self):
        return f"Estimate {self.estimate_number} - {self.claim.claim_number}"
    
    @property
    def variance_percentage(self):
        """Calculate variance between estimated and actual"""
        if self.actual_settlement_amount and self.actual_settlement_amount > 0:
            variance = abs(self.estimated_cost - self.actual_settlement_amount)
            return float((variance / self.actual_settlement_amount) * 100)
        return None
    
    @property
    def is_within_tolerance(self):
        """Check if estimate is within 20% of actual"""
        if self.variance_percentage is not None:
            return self.variance_percentage <= 20
        return None
    
    @property
    def needs_review(self):
        """Determine if estimate needs manual review"""
        return self.processing_recommendation in ['MANUAL_REVIEW', 'DETAILED_INVESTIGATION']
    
    def calculate_final_estimate(self):
        """Calculate final estimate with manual adjustments"""
        return self.estimated_cost + self.manual_adjustment
    
    def save(self, *args, **kwargs):
        """Update final estimate on save"""
        self.final_estimate = self.calculate_final_estimate()
        
        # Calculate prediction accuracy if actual amount is available
        if self.actual_settlement_amount and self.actual_settlement_amount > 0:
            variance = abs(self.estimated_cost - self.actual_settlement_amount)
            self.prediction_accuracy = float(
                100 - (variance / self.actual_settlement_amount * 100)
            )
        
        super().save(*args, **kwargs)


class ClaimProcessingLog(models.Model):
    """
    Log of automated claim processing actions
    Tracks all automated decisions and recommendations
    """
    ACTION_CHOICES = [
        ('ESTIMATE_GENERATED', 'Estimate Generated'),
        ('TRIAGE_ASSIGNED', 'Triage Priority Assigned'),
        ('RECOMMENDATION_MADE', 'Processing Recommendation Made'),
        ('RESERVE_CALCULATED', 'Reserve Amount Calculated'),
        ('MANUAL_REVIEW_TRIGGERED', 'Manual Review Triggered'),
        ('AUTO_APPROVED', 'Auto Approved'),
        ('FRAUD_FLAG_RAISED', 'Fraud Flag Raised'),
        ('ESTIMATE_UPDATED', 'Estimate Updated'),
        ('COST_RECALCULATED', 'Cost Recalculated'),
    ]

    # Primary identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships
    claim = models.ForeignKey(
        Claim,
        on_delete=models.CASCADE,
        related_name='processing_logs'
    )
    estimate = models.ForeignKey(
        ClaimEstimate,
        on_delete=models.CASCADE,
        related_name='processing_logs',
        null=True,
        blank=True
    )
    
    # Action details
    action_type = models.CharField(max_length=30, choices=ACTION_CHOICES)
    action_description = models.TextField()
    
    # System vs Manual
    is_automated = models.BooleanField(default=True)
    performed_by = models.CharField(
        max_length=100,
        default='SYSTEM',
        help_text="User or SYSTEM"
    )
    
    # Results
    result_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Detailed results of the action"
    )
    
    # Impact
    previous_value = models.CharField(max_length=200, blank=True, null=True)
    new_value = models.CharField(max_length=200, blank=True, null=True)
    
    # Metadata
    processing_time_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text="Time taken to process action (milliseconds)"
    )
    model_version = models.CharField(max_length=20, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'claim_processing_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['claim']),
            models.Index(fields=['estimate']),
            models.Index(fields=['action_type']),
            models.Index(fields=['is_automated']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = 'Claim Processing Log'
        verbose_name_plural = 'Claim Processing Logs'

    def __str__(self):
        return f"{self.action_type} - {self.claim.claim_number} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"