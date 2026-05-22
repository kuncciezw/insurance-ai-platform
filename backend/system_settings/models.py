"""
system_settings/models.py

Singleton model that holds every admin-configurable pricing value,
workflow threshold, and currency setting.  All other apps import
this and call  GlobalPricingSettings.get_solo()  instead of using
hard-coded numbers.
"""

from decimal import Decimal
from django.db import models
from solo.models import SingletonModel


class GlobalPricingSettings(SingletonModel):
    """
    One-row configuration table managed through Django Admin.
    Use  GlobalPricingSettings.get_solo()  everywhere you need a value.
    """

    # ── Base Rates ────────────────────────────────────────────────────────
    base_premium_percentage = models.DecimalField(
        max_digits=5, decimal_places=4, default=Decimal('0.05'),
        help_text="Percentage of vehicle market value used as the base premium (e.g. 0.05 = 5 %)"
    )
    minimum_premium = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('100.00'),
        help_text="Absolute minimum premium charged on any policy"
    )
    labour_rate_per_hour = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('75.00'),
        help_text="Repair labour rate used in claims cost estimation"
    )

    # ── Add-on Coverage Flat Fees ─────────────────────────────────────────
    addon_roadside_assistance = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('50.00'),
        help_text="Flat fee added to premium for roadside-assistance cover"
    )
    addon_rental_coverage = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('75.00'),
        help_text="Flat fee added to premium for rental-car cover"
    )
    addon_glass_coverage = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('30.00'),
        help_text="Flat fee added to premium for glass/windscreen cover"
    )

    # ── Risk Surcharges (as a fraction of ML-predicted premium) ──────────
    surcharge_young_driver = models.DecimalField(
        max_digits=5, decimal_places=4, default=Decimal('0.15'),
        help_text="Surcharge for drivers under 25 (e.g. 0.15 = +15 %)"
    )
    surcharge_senior_driver = models.DecimalField(
        max_digits=5, decimal_places=4, default=Decimal('0.10'),
        help_text="Surcharge for drivers over 65 (e.g. 0.10 = +10 %)"
    )
    surcharge_poor_credit = models.DecimalField(
        max_digits=5, decimal_places=4, default=Decimal('0.20'),
        help_text="Surcharge when credit score < 600 (e.g. 0.20 = +20 %)"
    )

    # ── Discounts (as a fraction of ML-predicted premium) ─────────────────
    discount_excellent_credit = models.DecimalField(
        max_digits=5, decimal_places=4, default=Decimal('0.10'),
        help_text="Discount when credit score ≥ 750 (e.g. 0.10 = −10 %)"
    )
    discount_anti_theft = models.DecimalField(
        max_digits=5, decimal_places=4, default=Decimal('0.05'),
        help_text="Discount when vehicle has an anti-theft device (e.g. 0.05 = −5 %)"
    )

    # ── Workflow Thresholds ───────────────────────────────────────────────
    threshold_auto_approve = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('1000.00'),
        help_text="Claims at or below this amount are auto-approved"
    )
    threshold_manual_review = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('5000.00'),
        help_text="Claims above this amount are escalated to manual review"
    )
    threshold_fraud_reject = models.FloatField(
        default=0.50,
        help_text="ML fraud-score at which a claim is auto-rejected (0 – 1)"
    )
    threshold_variance_warning = models.FloatField(
        default=0.20,
        help_text="Fraud-score / variance level that triggers a warning review (0 – 1)"
    )

    # ── Severity Multipliers (fraction of vehicle value) ──────────────────
    sev_trivial_mult = models.DecimalField(
        max_digits=4, decimal_places=3, default=Decimal('0.050'),
        help_text="'Trivial Damage' claim = this × vehicle value"
    )
    sev_minor_mult = models.DecimalField(
        max_digits=4, decimal_places=3, default=Decimal('0.150'),
        help_text="'Minor Damage' claim = this × vehicle value"
    )
    sev_major_mult = models.DecimalField(
        max_digits=4, decimal_places=3, default=Decimal('0.350'),
        help_text="'Major Damage' claim = this × vehicle value"
    )
    sev_total_mult = models.DecimalField(
        max_digits=4, decimal_places=3, default=Decimal('1.000'),
        help_text="'Total Loss' claim = this × vehicle value (typically 1.0)"
    )
    
    sev_moderate_mult = models.DecimalField(
        max_digits=4, decimal_places=3, default=Decimal('0.300'),
        help_text="'Moderate' damage claim = this × vehicle value"
   )

    # ── Cost-Breakdown Ratios (must sum to 1.0) ───────────────────────────
    ratio_vehicle_damage = models.DecimalField(
        max_digits=3, decimal_places=2, default=Decimal('0.60'),
        help_text="Portion of estimated cost attributed to vehicle damage"
    )
    ratio_medical_expenses = models.DecimalField(
        max_digits=3, decimal_places=2, default=Decimal('0.20'),
        help_text="Portion attributed to medical expenses"
    )
    ratio_legal_fees = models.DecimalField(
        max_digits=3, decimal_places=2, default=Decimal('0.10'),
        help_text="Portion attributed to legal fees"
    )
    ratio_other_costs = models.DecimalField(
        max_digits=3, decimal_places=2, default=Decimal('0.10'),
        help_text="Portion attributed to other costs"
    )

    # ── Currency Settings ─────────────────────────────────────────────────
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar (USD)'),
        ('ZWG', 'Zimbabwe Gold (ZWG)'),
    ]
    default_currency = models.CharField(
        max_length=3, choices=CURRENCY_CHOICES, default='USD',
        help_text="Default currency applied to new policies and quotes"
    )
    zwg_usd_exchange_rate = models.DecimalField(
        max_digits=12, decimal_places=4, default=Decimal('13.5600'),
        help_text="ZWG per 1 USD — used for display conversion (e.g. 13.56)"
    )
    allow_multi_currency = models.BooleanField(
        default=True,
        help_text="Allow users to select ZWG in addition to USD when creating policies"
    )
    
    # ── Age-based Risk Thresholds ─────────────────────────────────────────
    age_threshold_young_driver = models.IntegerField(
        default=25,
        help_text="Age below which young driver surcharge applies"
    )
    age_threshold_senior_driver = models.IntegerField(
        default=65,
        help_text="Age above which senior driver surcharge applies"
    )

    # ── Credit Score Thresholds ───────────────────────────────────────────
    credit_threshold_poor = models.IntegerField(
        default=600,
        help_text="Credit score below which poor credit surcharge applies"
    )
    credit_threshold_excellent = models.IntegerField(
        default=750,
        help_text="Credit score at/above which excellent credit discount applies"
    )

    # ── Vehicle Risk Thresholds ───────────────────────────────────────────
    vehicle_age_threshold_old = models.IntegerField(
        default=10,
        help_text="Vehicle age (years) above which old vehicle surcharge applies"
    )
    surcharge_old_vehicle = models.DecimalField(
        max_digits=5, decimal_places=4, default=Decimal('0.10'),
        help_text="Surcharge for vehicles older than threshold (e.g. 0.10 = +10%)"
    )
    surcharge_modified_vehicle = models.DecimalField(
        max_digits=5, decimal_places=4, default=Decimal('0.15'),
        help_text="Surcharge for modified vehicles (e.g. 0.15 = +15%)"
    )

    # ── Loyalty Discount ──────────────────────────────────────────────────
    loyalty_years_threshold = models.IntegerField(
        default=5,
        help_text="Years with company required for loyalty discount"
    )
    discount_loyalty = models.DecimalField(
        max_digits=5, decimal_places=4, default=Decimal('0.10'),
        help_text="Loyalty discount percentage (e.g. 0.10 = -10%)"
    )

    # ── Coverage Limits ───────────────────────────────────────────────────
    minimum_coverage_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('1000.00'),
        help_text="Minimum allowable coverage amount for any policy"
    )

    class Meta:
        verbose_name = "Global Pricing Settings"
        verbose_name_plural = "Global Pricing Settings"

    def __str__(self) -> str:
        return "Global Pricing Settings"