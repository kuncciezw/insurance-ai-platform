"""
system_settings/admin.py

Registers GlobalPricingSettings as a Singleton admin page with
clearly labelled, collapsible fieldset sections.
"""

from django.contrib import admin
from solo.admin import SingletonModelAdmin
from .models import GlobalPricingSettings


@admin.register(GlobalPricingSettings)
class GlobalPricingSettingsAdmin(SingletonModelAdmin):
    """
    Admin interface for the singleton pricing / workflow configuration.
    Sections map 1-to-1 with the logical groups in models.py.
    """

    fieldsets = (
        # ── Base Rates ────────────────────────────────────────────────
        ('Base Rates', {
            'description': 'Fundamental pricing inputs applied to every policy.',
            'fields': (
                'base_premium_percentage',
                'minimum_premium',
                'labor_rate_per_hour',
            ),
        }),

        # ── Add-on Coverages ─────────────────────────────────────────
        ('Add-on Coverage Fees', {
            'description': 'Flat fees added to the premium when optional coverages are selected.',
            'fields': (
                'addon_roadside_assistance',
                'addon_rental_coverage',
                'addon_glass_coverage',
            ),
        }),

        # ── Surcharges ────────────────────────────────────────────────
        ('Risk Surcharges', {
            'description': (
                'Expressed as a decimal fraction of the ML-predicted premium '
                '(e.g. 0.15 = +15 %).'
            ),
            'fields': (
                'surcharge_young_driver',
                'surcharge_senior_driver',
                'surcharge_poor_credit',
            ),
        }),

        # ── Discounts ─────────────────────────────────────────────────
        ('Discounts', {
            'description': 'Expressed as a decimal fraction of the ML-predicted premium.',
            'fields': (
                'discount_excellent_credit',
                'discount_anti_theft',
            ),
        }),

        # ── Workflow Thresholds ───────────────────────────────────────
        ('Workflow Thresholds', {
            'description': (
                'Dollar amounts control auto-approve / manual-review routing. '
                'Fraud scores (0 – 1) control the ML pipeline decisions.'
            ),
            'fields': (
                'threshold_auto_approve',
                'threshold_manual_review',
                'threshold_fraud_reject',
                'threshold_variance_warning',
            ),
        }),

        # ── Severity Multipliers ──────────────────────────────────────
        ('Severity Multipliers', {
            'description': 'Fraction of vehicle market value used when auto-calculating claimed amounts.',
            'classes': ('collapse',),
            'fields': (
                'sev_trivial_mult',
                'sev_minor_mult',
                'sev_major_mult',
                'sev_total_mult',
            ),
        }),

        # ── Cost-Breakdown Ratios ─────────────────────────────────────
        ('Cost-Breakdown Ratios', {
            'description': 'Must sum to 1.0.  Used to split an estimated claim total into categories.',
            'classes': ('collapse',),
            'fields': (
                'ratio_vehicle_damage',
                'ratio_medical_expenses',
                'ratio_legal_fees',
                'ratio_other_costs',
            ),
        }),

        # ── Currency Settings ─────────────────────────────────────────
        ('Currency Settings', {
            'description': 'Controls the default currency and ZWG ↔ USD conversion rate.',
            'fields': (
                'default_currency',
                'zwg_usd_exchange_rate',
                'allow_multi_currency',
            ),
        }),
    )