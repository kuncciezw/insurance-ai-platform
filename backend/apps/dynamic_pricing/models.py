"""
Models for Dynamic Pricing Application
Includes Quote and PriceHistory models
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid
from apps.fraud_detection.models import Policyholder, Vehicle, Policy


class Quote(models.Model):
    """
    Insurance Quote model for price estimation
    """
    QUOTE_STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('CALCULATED', 'Calculated'),
        ('SENT', 'Sent to Customer'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('EXPIRED', 'Expired'),
        ('CONVERTED', 'Converted to Policy'),
    ]
    
    POLICY_TYPE_CHOICES = [
        ('COMPREHENSIVE', 'Comprehensive'),
        ('THIRD_PARTY', 'Third Party'),
        ('COLLISION', 'Collision'),
        ('LIABILITY', 'Liability'),
    ]
    
    COVERAGE_LEVEL_CHOICES = [
        ('BASIC', 'Basic'),
        ('STANDARD', 'Standard'),
        ('PREMIUM', 'Premium'),
    ]

    # Primary identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quote_number = models.CharField(max_length=20, unique=True, db_index=True)
    
    # Relationships (optional - for existing customers)
    policyholder = models.ForeignKey(
        Policyholder,
        on_delete=models.CASCADE,
        related_name='quotes',
        null=True,
        blank=True
    )
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='quotes',
        null=True,
        blank=True
    )
    
    # Quote details
    policy_type = models.CharField(max_length=20, choices=POLICY_TYPE_CHOICES)
    coverage_level = models.CharField(max_length=20, choices=COVERAGE_LEVEL_CHOICES)
    status = models.CharField(max_length=20, choices=QUOTE_STATUS_CHOICES, default='DRAFT')
    
    # Customer information (for new customers)
    customer_age = models.IntegerField(
        validators=[MinValueValidator(18), MaxValueValidator(100)],
        null=True,
        blank=True
    )
    customer_credit_score = models.IntegerField(
        validators=[MinValueValidator(300), MaxValueValidator(850)],
        null=True,
        blank=True
    )
    customer_years_experience = models.IntegerField(
        validators=[MinValueValidator(0)],
        default=0
    )
    
    # Vehicle information (for new vehicles)
    vehicle_year = models.IntegerField(
        validators=[MinValueValidator(1900), MaxValueValidator(2030)],
        null=True,
        blank=True
    )
    vehicle_make = models.CharField(max_length=50, blank=True, null=True)
    vehicle_model = models.CharField(max_length=50, blank=True, null=True)
    vehicle_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        null=True,
        blank=True
    )
    vehicle_has_anti_theft = models.BooleanField(default=False)
    vehicle_is_modified = models.BooleanField(default=False)
    
    # Coverage details
    coverage_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    deductible = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Pricing (calculated by ML model)
    base_premium = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    risk_adjustment = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Additional premium based on risk factors"
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    final_premium = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # ML model information
    ml_predicted_premium = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Premium predicted by ML model"
    )
    confidence_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Model confidence in prediction (0-1)"
    )
    
    # Risk factors breakdown (JSON field for flexibility)
    risk_factors = models.JSONField(
        default=dict,
        blank=True,
        help_text="Breakdown of risk factors affecting price"
    )
    
    # Additional options
    has_roadside_assistance = models.BooleanField(default=False)
    has_rental_coverage = models.BooleanField(default=False)
    has_glass_coverage = models.BooleanField(default=False)
    
    # Validity
    valid_until = models.DateField(null=True, blank=True)
    
    # Conversion tracking
    converted_policy = models.ForeignKey(
        Policy,
        on_delete=models.SET_NULL,
        related_name='source_quote',
        null=True,
        blank=True
    )
    
    # Notes and metadata
    notes = models.TextField(blank=True, null=True)
    customer_email = models.EmailField(blank=True, null=True)
    customer_phone = models.CharField(max_length=15, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'quotes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['quote_number']),
            models.Index(fields=['status']),
            models.Index(fields=['policyholder']),
            models.Index(fields=['vehicle']),
            models.Index(fields=['created_at']),
            models.Index(fields=['valid_until']),
        ]
        verbose_name = 'Quote'
        verbose_name_plural = 'Quotes'

    def __str__(self):
        if self.policyholder:
            return f"Quote {self.quote_number} - {self.policyholder.full_name}"
        return f"Quote {self.quote_number}"
    
    @property
    def is_valid(self):
        """Check if quote is still valid"""
        from datetime import date
        if self.valid_until:
            return self.status in ['CALCULATED', 'SENT'] and self.valid_until >= date.today()
        return False
    
    @property
    def days_until_expiry(self):
        """Days until quote expires"""
        from datetime import date
        if self.valid_until and self.valid_until > date.today():
            return (self.valid_until - date.today()).days
        return 0
    
    def calculate_total_premium(self):
        """Calculate total premium with adjustments"""
        total = self.base_premium + self.risk_adjustment - self.discount_amount
        
        # Add optional coverages
        if self.has_roadside_assistance:
            total += Decimal('50.00')
        if self.has_rental_coverage:
            total += Decimal('75.00')
        if self.has_glass_coverage:
            total += Decimal('30.00')
        
        return max(total, Decimal('0.00'))


class PriceHistory(models.Model):
    """
    Track pricing history for policies over time
    """
    CHANGE_REASON_CHOICES = [
        ('NEW_POLICY', 'New Policy'),
        ('RENEWAL', 'Policy Renewal'),
        ('RISK_CHANGE', 'Risk Profile Change'),
        ('CLAIM_FILED', 'Claim Filed'),
        ('MARKET_ADJUSTMENT', 'Market Adjustment'),
        ('MANUAL_ADJUSTMENT', 'Manual Adjustment'),
        ('DISCOUNT_APPLIED', 'Discount Applied'),
        ('COVERAGE_CHANGE', 'Coverage Change'),
    ]

    # Primary identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships
    policy = models.ForeignKey(
        Policy,
        on_delete=models.CASCADE,
        related_name='price_history'
    )
    quote = models.ForeignKey(
        Quote,
        on_delete=models.SET_NULL,
        related_name='price_history',
        null=True,
        blank=True
    )
    
    # Price information
    previous_premium = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        null=True,
        blank=True
    )
    new_premium = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    premium_change = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    premium_change_percentage = models.FloatField(
        default=0.0,
        help_text="Percentage change in premium"
    )
    
    # Change details
    change_reason = models.CharField(max_length=30, choices=CHANGE_REASON_CHOICES)
    change_description = models.TextField(blank=True, null=True)
    
    # Risk factors at this point in time
    risk_score_snapshot = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    risk_factors_snapshot = models.JSONField(
        default=dict,
        blank=True,
        help_text="Risk factors at time of pricing"
    )
    
    # Effective dates
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    
    # Metadata
    created_by = models.CharField(max_length=100, default='SYSTEM')
    notes = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'price_history'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['policy']),
            models.Index(fields=['effective_from', 'effective_to']),
            models.Index(fields=['change_reason']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = 'Price History'
        verbose_name_plural = 'Price Histories'

    def __str__(self):
        return f"Price History - {self.policy.policy_number} ({self.effective_from})"
    
    @property
    def is_current(self):
        """Check if this is the current pricing"""
        from datetime import date
        today = date.today()
        if self.effective_to:
            return self.effective_from <= today <= self.effective_to
        return self.effective_from <= today
    
    def save(self, *args, **kwargs):
        """Calculate premium change on save"""
        if self.previous_premium and self.new_premium:
            self.premium_change = self.new_premium - self.previous_premium
            if self.previous_premium > 0:
                self.premium_change_percentage = float(
                    (self.premium_change / self.previous_premium) * 100
                )
        super().save(*args, **kwargs)