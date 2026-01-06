"""
Models for Fraud Detection Application
Includes Policyholders, Vehicles, Policies, and Claims
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

    # Primary identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    policy_holder_id = models.CharField(max_length=20, unique=True, db_index=True)
    
    # Personal information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    
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
    
    # Address information
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='USA')
    
    # Demographics and risk factors
    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS_CHOICES)
    occupation = models.CharField(max_length=50, choices=OCCUPATION_CHOICES)
    annual_income = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Credit and history
    credit_score = models.IntegerField(
        validators=[MinValueValidator(300), MaxValueValidator(850)],
        help_text="Credit score between 300 and 850"
    )
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

    # Primary identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehicle_id = models.CharField(max_length=20, unique=True, db_index=True)
    
    # Vehicle details
    make = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    year = models.IntegerField(
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
            models.Index(fields=['vehicle_id']),
            models.Index(fields=['vin']),
            models.Index(fields=['registration_number']),
            models.Index(fields=['policyholder']),
        ]
        verbose_name = 'Vehicle'
        verbose_name_plural = 'Vehicles'

    def __str__(self):
        return f"{self.year} {self.make} {self.model} ({self.vehicle_id})"
    
    @property
    def vehicle_age(self):
        from datetime import date
        return date.today().year - self.year


class Policy(models.Model):
    """
    Insurance Policy model
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
    
    # Financial details
    premium_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
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
    
    # Dates
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


class Claim(models.Model):
    """
    Insurance Claim model
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

    # Primary identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    claim_number = models.CharField(max_length=20, unique=True, db_index=True)
    
    # Relationships
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
    claim_status = models.CharField(max_length=20, choices=CLAIM_STATUS_CHOICES, default='SUBMITTED')
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    
    # Incident information
    incident_date = models.DateTimeField()
    incident_location = models.CharField(max_length=255)
    incident_description = models.TextField()
    
    # Police and witness information
    police_report_filed = models.BooleanField(default=False)
    police_report_number = models.CharField(max_length=50, blank=True, null=True)
    witnesses_present = models.BooleanField(default=False)
    number_of_witnesses = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    
    # Parties involved
    number_of_vehicles_involved = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    number_of_injuries = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    third_party_involved = models.BooleanField(default=False)
    
    # Financial details
    claimed_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    approved_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    paid_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Fraud indicators (will be populated by ML model)
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