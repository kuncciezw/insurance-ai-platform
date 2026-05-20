"""
Models for Fraud Detection Application
Updated with requested changes:
- Removed postal_code
- Added license fields to Policyholder
- Changed Vehicle.year to manufacture_year
- Removed vehicle_id
- Added currency to Policy
- Removed Claims fields: number_of_injuries, police_report_filed, witnesses_present, third_party_involved
- Added payment_method to Claims
- Added incident_evidence file field to Claims
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.contrib.auth.models import User
from decimal import Decimal
import uuid


class Policyholder(models.Model):
    """
    Policyholder model representing insurance customers
    """
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    MARITAL_STATUS_CHOICES = [
        ('SINGLE', 'Single'),
        ('MARRIED', 'Married'),
        ('DIVORCED', 'Divorced'),
        ('WIDOWED', 'Widowed'),
    ]
    
    OCCUPATION_CHOICES = [
        ('EMPLOYED', 'Employed'),
        ('SELF_EMPLOYED', 'Self Employed'),
        ('UNEMPLOYED', 'Unemployed'),
        ('RETIRED', 'Retired'),
        ('STUDENT', 'Student'),
    ]

    CREDIT_RATING_CHOICES = [
        ('EXCELLENT', 'Excellent (750-850)'),
        ('GOOD', 'Good (700-749)'),
        ('FAIR', 'Fair (650-699)'),
        ('POOR', 'Poor (600-649)'),
        ('VERY_POOR', 'Very Poor (300-599)'),
    ]

    # Primary identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    policy_holder_id = models.CharField(max_length=20, unique=True, db_index=True)
    
    # Personal information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    national_id = models.CharField(max_length=20, blank=True, null=True)
    
    # Contact information
    email = models.EmailField(unique=True, db_index=True)
    phone_number = models.CharField(
        max_length=15,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ]
    )
    
    # Address information (postal_code removed)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='Zimbabwe')
    
    # Demographics and risk factors
    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS_CHOICES)
    occupation = models.CharField(max_length=50, choices=OCCUPATION_CHOICES)
    monthly_income = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        default=Decimal('0.00')
    )
    
    # Credit information (auto-calculated)
    credit_score = models.IntegerField(
        validators=[MinValueValidator(300), MaxValueValidator(850)],
        help_text="Auto-calculated credit score between 300 and 850",
        null=True,
        blank=True
    )
    credit_rating = models.CharField(
        max_length=20, 
        choices=CREDIT_RATING_CHOICES,
        help_text="Auto-calculated based on credit score",
        null=True,
        blank=True
    )
    
    # License validation fields (NEW)
    has_driving_license = models.BooleanField(default=False, help_text="Has valid driving license")
    has_defensive_license = models.BooleanField(default=False, help_text="Has defensive driving certificate")
    is_medical_license_valid = models.BooleanField(default=True, help_text="Medical fitness certificate is valid")
    
    # Company history
    years_with_company = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Number of years as customer"
    )
    
    # Account status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'policyholders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['policy_holder_id']),
            models.Index(fields=['last_name', 'first_name']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = 'Policyholder'
        verbose_name_plural = 'Policyholders'

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.policy_holder_id})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    @property
    def annual_income(self):
        """Calculate annual income from monthly income"""
        return self.monthly_income * 12
    
    def calculate_credit_score(self):
        """Auto-calculate credit score based on various factors"""
        base_score = 650  # Default starting score
        
        # Income factor (higher income = better score)
        if self.monthly_income >= 5000:
            base_score += 50
        elif self.monthly_income >= 3000:
            base_score += 30
        elif self.monthly_income >= 1500:
            base_score += 10
        
        # Years with company (loyalty bonus)
        base_score += min(self.years_with_company * 5, 50)
        
        # License checks
        if self.has_driving_license:
            base_score += 20
        if self.has_defensive_license:
            base_score += 15
        if not self.is_medical_license_valid:
            base_score -= 30
        
        # Check claims history
        from apps.fraud_detection.models import Claim
        claims_count = Claim.objects.filter(policyholder=self).count()
        fraudulent_claims = Claim.objects.filter(policyholder=self, is_fraudulent=True).count()
        
        if fraudulent_claims > 0:
            base_score -= fraudulent_claims * 50
        elif claims_count > 3:
            base_score -= (claims_count - 3) * 10
        
        # Ensure within valid range
        return max(300, min(850, base_score))
    
    def calculate_credit_rating(self):
        """Auto-calculate credit rating based on credit score"""
        score = self.credit_score or self.calculate_credit_score()
        
        if score >= 750:
            return 'EXCELLENT'
        elif score >= 700:
            return 'GOOD'
        elif score >= 650:
            return 'FAIR'
        elif score >= 600:
            return 'POOR'
        else:
            return 'VERY_POOR'
    
    def save(self, *args, **kwargs):
        """Auto-calculate credit score and rating on save"""
        if not self.credit_score:
            self.credit_score = self.calculate_credit_score()
        self.credit_rating = self.calculate_credit_rating()
        super().save(*args, **kwargs)


class Vehicle(models.Model):
    """
    Vehicle model representing insured vehicles
    """
    FUEL_TYPE_CHOICES = [
        ('PETROL', 'Petrol'),
        ('DIESEL', 'Diesel'),
        ('ELECTRIC', 'Electric'),
        ('HYBRID', 'Hybrid'),
        ('CNG', 'CNG'),
    ]
    
    VEHICLE_TYPE_CHOICES = [
        ('SEDAN', 'Sedan'),
        ('SUV', 'SUV'),
        ('TRUCK', 'Truck'),
        ('VAN', 'Van'),
        ('COUPE', 'Coupe'),
        ('HATCHBACK', 'Hatchback'),
        ('SPORTS', 'Sports Car'),
    ]

    # Primary identification (vehicle_id removed)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Vehicle details
    make = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    manufacture_year = models.IntegerField(  # Changed from 'year'
        validators=[MinValueValidator(1900), MaxValueValidator(2030)]
    )
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPE_CHOICES)
    
    # Identification numbers
    vin = models.CharField(
        max_length=17,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[A-HJ-NPR-Z0-9]{17}$',
                message="VIN must be 17 characters (excluding I, O, Q)"
            )
        ],
        help_text="Vehicle Identification Number"
    )
    registration_number = models.CharField(max_length=20, unique=True)
    
    # Technical specifications
    engine_capacity = models.IntegerField(
        validators=[MinValueValidator(500)],
        help_text="Engine capacity in CC"
    )
    fuel_type = models.CharField(max_length=20, choices=FUEL_TYPE_CHOICES)
    seating_capacity = models.IntegerField(
        validators=[MinValueValidator(2), MaxValueValidator(50)]
    )
    
    # Value and condition
    market_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    odometer_reading = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Current odometer reading in miles"
    )
    
    # Safety and modifications
    has_anti_theft = models.BooleanField(default=False)
    has_airbags = models.BooleanField(default=True)
    has_abs = models.BooleanField(default=True)
    is_modified = models.BooleanField(default=False)
    
    # Ownership
    policyholder = models.ForeignKey(
        Policyholder,
        on_delete=models.CASCADE,
        related_name='vehicles'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'vehicles'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['vin']),
            models.Index(fields=['registration_number']),
            models.Index(fields=['policyholder']),
        ]
        verbose_name = 'Vehicle'
        verbose_name_plural = 'Vehicles'

    def __str__(self):
        return f"{self.manufacture_year} {self.make} {self.model}"
    
    @property
    def vehicle_age(self):
        from datetime import date
        return date.today().year - self.manufacture_year


class Policy(models.Model):
    """
    Insurance Policy model with auto-calculated premiums
    """
    POLICY_TYPE_CHOICES = [
        ('COMPREHENSIVE', 'Comprehensive'),
        ('THIRD_PARTY', 'Third Party'),
        ('COLLISION', 'Collision'),
        ('LIABILITY', 'Liability'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('EXPIRED', 'Expired'),
        ('CANCELLED', 'Cancelled'),
        ('SUSPENDED', 'Suspended'),
        ('PENDING', 'Pending'),
    ]
    
    COVERAGE_LEVEL_CHOICES = [
        ('BASIC', 'Basic'),
        ('STANDARD', 'Standard'),
        ('PREMIUM', 'Premium'),
    ]
    
    CURRENCY_CHOICES = [  # NEW
        ('USD', 'US Dollar'),
        ('ZWG', 'Zimbabwe Gold'),
    ]

    # Primary identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    policy_number = models.CharField(max_length=20, unique=True, db_index=True)
    
    # Relationships
    policyholder = models.ForeignKey(
        Policyholder,
        on_delete=models.CASCADE,
        related_name='policies'
    )
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='policies'
    )
    
    # Policy details
    policy_type = models.CharField(max_length=20, choices=POLICY_TYPE_CHOICES)
    coverage_level = models.CharField(max_length=20, choices=COVERAGE_LEVEL_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')  # NEW
    
    # Financial details (auto-calculated)
    premium_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Auto-calculated premium amount",
        null=True,
        blank=True
    )
    coverage_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Auto-calculated coverage amount",
        null=True,
        blank=True
    )
    deductible = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Auto-calculated deductible amount",
        null=True,
        blank=True
    )
    
    # Dates (start_date defaults to today)
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Additional coverage options
    has_roadside_assistance = models.BooleanField(default=False)
    has_rental_coverage = models.BooleanField(default=False)
    has_glass_coverage = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'policies'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['policy_number']),
            models.Index(fields=['status']),
            models.Index(fields=['policyholder']),
            models.Index(fields=['vehicle']),
            models.Index(fields=['start_date', 'end_date']),
        ]
        verbose_name = 'Policy'
        verbose_name_plural = 'Policies'

    def __str__(self):
        return f"Policy {self.policy_number} - {self.policyholder.full_name}"
    
    @property
    def is_active(self):
        from datetime import date
        today = date.today()
        return self.status == 'ACTIVE' and self.start_date <= today <= self.end_date
    
    @property
    def days_until_expiry(self):
        from datetime import date
        if self.end_date > date.today():
            return (self.end_date - date.today()).days
        return 0
    
    def calculate_premium(self):
        """Auto-calculate premium based on multiple factors & Global Settings"""
        from system_settings.models import GlobalPricingSettings
        settings = GlobalPricingSettings.get_solo()
        
        # Base premium based on vehicle value and global percentage (e.g., 5%)
        base_premium = float(self.vehicle.market_value) * float(settings.base_premium_percentage)
        
        # Coverage level multiplier
        coverage_multipliers = {
            'BASIC': 1.0,
            'STANDARD': 1.3,
            'PREMIUM': 1.6
        }
        base_premium *= coverage_multipliers.get(self.coverage_level, 1.0)
        
        # Policy type multiplier
        policy_multipliers = {
            'COMPREHENSIVE': 1.5,
            'THIRD_PARTY': 0.7,
            'COLLISION': 1.2,
            'LIABILITY': 0.8
        }
        base_premium *= policy_multipliers.get(self.policy_type, 1.0)
        
        # Vehicle age factor
        vehicle_age = self.vehicle.vehicle_age
        if vehicle_age > 10:
            base_premium *= 0.7
        elif vehicle_age > 5:
            base_premium *= 0.85
        
        # Driver risk factors (Dynamic Surcharges)
        driver_age = self.policyholder.age
        if driver_age < 25:
            base_premium *= (1.0 + float(settings.surcharge_young_driver))
        elif driver_age > 65:
            base_premium *= (1.0 + float(settings.surcharge_senior_driver))
        
        # Credit score adjustments (Dynamic Discounts/Surcharges)
        credit_score = self.policyholder.credit_score or 650
        if credit_score >= 750:
            base_premium *= (1.0 - float(settings.discount_excellent_credit))
        elif credit_score >= 700:
            base_premium *= 0.92  # Secondary tier discount
        elif credit_score < 600:
            base_premium *= (1.0 + float(settings.surcharge_poor_credit))
        
        # License & Medical factors
        if self.policyholder.has_defensive_license:
            base_premium *= 0.9 
        if not self.policyholder.has_driving_license:
            base_premium *= 1.5 
        if not self.policyholder.is_medical_license_valid:
            base_premium *= 1.2 
        
        # Safety features (Dynamic Anti-Theft)
        if self.vehicle.has_anti_theft:
            base_premium *= (1.0 - float(settings.discount_anti_theft))
        if self.vehicle.has_airbags:
            base_premium *= 0.93
        if self.vehicle.has_abs:
            base_premium *= 0.95
        
        # Modified vehicle surcharge
        if self.vehicle.is_modified:
            base_premium *= 1.25
        
        # Dynamic Additional coverage add-ons
        if self.has_roadside_assistance:
            base_premium += float(settings.addon_roadside_assistance)
        if self.has_rental_coverage:
            base_premium += float(settings.addon_rental_coverage)
        if self.has_glass_coverage:
            base_premium += float(settings.addon_glass_coverage)
        
        # Enforce Global Minimum Premium Floor
        final_premium = max(base_premium, float(settings.minimum_premium))
        
        return Decimal(str(round(final_premium, 2)))
    
    def calculate_coverage(self):
        """Auto-calculate coverage amount"""
        # Coverage is based on vehicle value and coverage level
        vehicle_value = float(self.vehicle.market_value)
        
        coverage_percentages = {
            'BASIC': 0.8,      # 80% of vehicle value
            'STANDARD': 1.0,   # 100% of vehicle value
            'PREMIUM': 1.2     # 120% of vehicle value
        }
        
        coverage_multiplier = coverage_percentages.get(self.coverage_level, 1.0)
        coverage = vehicle_value * coverage_multiplier
        
        return Decimal(str(round(coverage, 2)))
    
    def calculate_deductible(self):
        """Auto-calculate deductible amount"""
        # Deductible is typically 5-15% of coverage amount
        coverage = float(self.calculate_coverage())
        
        deductible_percentages = {
            'BASIC': 0.15,     # 15% deductible
            'STANDARD': 0.10,  # 10% deductible
            'PREMIUM': 0.05    # 5% deductible
        }
        
        deductible_pct = deductible_percentages.get(self.coverage_level, 0.10)
        deductible = coverage * deductible_pct
        
        return Decimal(str(round(deductible, 2)))
    
    def save(self, *args, **kwargs):
        """Auto-calculate financial amounts on save"""
        if not self.premium_amount:
            self.premium_amount = self.calculate_premium()
        if not self.coverage_amount:
            self.coverage_amount = self.calculate_coverage()
        if not self.deductible:
            self.deductible = self.calculate_deductible()
        super().save(*args, **kwargs)


class Claim(models.Model):
    """
    Insurance Claim model - streamlined version
    """
    CLAIM_TYPE_CHOICES = [
        ('ACCIDENT', 'Accident'),
        ('THEFT', 'Theft'),
        ('VANDALISM', 'Vandalism'),
        ('NATURAL_DISASTER', 'Natural Disaster'),
        ('FIRE', 'Fire'),
        ('OTHER', 'Other'),
    ]
    
    CLAIM_STATUS_CHOICES = [
        ('SUBMITTED', 'Submitted'),
        ('UNDER_REVIEW', 'Under Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('PAID', 'Paid'),
        ('CLOSED', 'Closed'),
    ]
    
    SEVERITY_CHOICES = [
        ('MINOR', 'Minor'),
        ('MODERATE', 'Moderate'),
        ('MAJOR', 'Major'),
        ('TOTAL_LOSS', 'Total Loss'),
    ]
    
    PAYMENT_METHOD_CHOICES = [  # NEW
        ('SWIPE', 'Swipe Card'),
        ('ECOCASH', 'EcoCash'),
        ('CASH', 'Cash'),
        ('BANK_TRANSFER', 'Bank Transfer'),
    ]

    # Primary identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    claim_number = models.CharField(max_length=20, unique=True, db_index=True)
    
    # Relationships (auto-populated from policy)
    policy = models.ForeignKey(
        Policy,
        on_delete=models.CASCADE,
        related_name='claims'
    )
    policyholder = models.ForeignKey(
        Policyholder,
        on_delete=models.CASCADE,
        related_name='claims'
    )
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='claims'
    )
    
    # Claim details
    claim_type = models.CharField(max_length=30, choices=CLAIM_TYPE_CHOICES)
    claim_status = models.CharField(
        max_length=20, 
        choices=CLAIM_STATUS_CHOICES, 
        default='SUBMITTED',
        help_text="Auto-determined from policy status"
    )
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    
    # Incident information
    incident_date = models.DateTimeField()
    incident_location = models.CharField(max_length=255)
    incident_evidence = models.FileField(  # NEW - replaces incident_description text
        upload_to='claim_evidence/',
        help_text="Upload evidence file (photos, documents, etc.)",
        null=True,
        blank=True
    )
    
    # Number of vehicles involved
    number_of_vehicles_involved = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    
    # Payment method (NEW)
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='BANK_TRANSFER',
        help_text="Preferred payment method for claim settlement"
    )
    
    # Financial details (auto-calculated)
    claimed_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Auto-calculated from damage assessment",
        null=True,
        blank=True
    )
    approved_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Auto-calculated based on policy coverage"
    )
    paid_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Auto-set when payment is processed"
    )
    
    # Fraud indicators (populated by ML model)
    fraud_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Fraud probability score from ML model (0-1)"
    )
    is_fraudulent = models.BooleanField(default=False)
    fraud_reason = models.TextField(blank=True, null=True)
    
    # Timestamps
    submitted_date = models.DateTimeField(auto_now_add=True)
    reviewed_date = models.DateTimeField(blank=True, null=True)
    closed_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'claims'
        ordering = ['-submitted_date']
        indexes = [
            models.Index(fields=['claim_number']),
            models.Index(fields=['claim_status']),
            models.Index(fields=['policy']),
            models.Index(fields=['policyholder']),
            models.Index(fields=['incident_date']),
            models.Index(fields=['is_fraudulent']),
            models.Index(fields=['fraud_score']),
        ]
        verbose_name = 'Claim'
        verbose_name_plural = 'Claims'

    def __str__(self):
        return f"Claim {self.claim_number} - {self.claim_type}"
    
    @property
    def days_since_submission(self):
        from datetime import datetime
        from django.utils import timezone
        now = timezone.now()
        return (now - self.submitted_date).days
    
    @property
    def processing_time(self):
        """Returns processing time in days if claim is closed"""
        if self.closed_date:
            return (self.closed_date - self.submitted_date).days
        return None
    
    def calculate_claimed_amount(self):
        """
        Auto-calculate claim amount based on severity and vehicle value.
        Uses admin-configurable severity multipliers from GlobalPricingSettings
        instead of hardcoded percentages.
        """
        from system_settings.models import GlobalPricingSettings
        settings = GlobalPricingSettings.get_solo()
 
        vehicle_value = float(self.vehicle.market_value)
 
        severity_multipliers = {
            'MINOR':      float(settings.sev_minor_mult),
            'MODERATE':   float(settings.sev_moderate_mult),   # new field — see note above
            'MAJOR':      float(settings.sev_major_mult),
            'TOTAL_LOSS': float(settings.sev_total_mult),
        }
 
        damage_pct = severity_multipliers.get(self.severity, float(settings.sev_minor_mult))
        claim_amount = vehicle_value * damage_pct
 
        # Cannot exceed policy coverage
        max_coverage = float(self.policy.coverage_amount)
        claim_amount = min(claim_amount, max_coverage)
 
        return Decimal(str(round(claim_amount, 2)))
    
    def auto_populate_from_policy(self):
        """Auto-populate policyholder and vehicle from selected policy"""
        if self.policy:
            self.policyholder = self.policy.policyholder
            self.vehicle = self.policy.vehicle
    
    def auto_update_claim_status(self):
        """Auto-determine claim status using Global Workflow Thresholds"""
        from system_settings.models import GlobalPricingSettings
        settings = GlobalPricingSettings.get_solo()
        
        if not self.policy.is_active:
            self.claim_status = 'REJECTED'
            
        # 1. Fraud ML Rejection Threshold
        elif self.fraud_score >= settings.threshold_fraud_reject:
            self.claim_status = 'REJECTED'
            self.fraud_reason = 'Auto-rejected: Exceeded global fraud threshold'
            
        # 2. Manual Review Trigger (High Variance/Risk or High Dollar Amount)
        elif self.fraud_score >= settings.threshold_variance_warning:
            self.claim_status = 'UNDER_REVIEW'
        elif self.claimed_amount and self.claimed_amount >= float(settings.threshold_manual_review):
            self.claim_status = 'UNDER_REVIEW'
            
        # 3. Auto-Approve Trigger (Low Risk AND Low Dollar Amount)
        elif self.claimed_amount and self.claimed_amount <= float(settings.threshold_auto_approve):
            self.claim_status = 'APPROVED'
            self.approved_amount = self.claimed_amount
            self.reviewed_date = self.submitted_date # Auto-reviewed immediately
        # Otherwise keep current status
    
    def save(self, *args, **kwargs):
        """Auto-populate and calculate fields on save."""
        self.auto_populate_from_policy()
    
        if not self.claimed_amount:
            self.claimed_amount = self.calculate_claimed_amount()
        
        super().save(*args, **kwargs)
