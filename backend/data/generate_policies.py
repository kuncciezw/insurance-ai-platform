"""
Generate synthetic insurance policy data - Zimbabwe Market
REFACTORED VERSION
- All vehicle age calculations use manufacture_year (renamed from year)
- Added currency field (80% USD, 20% ZWG)
- Premium calculated as 3-8% of vehicle market_value, adjusted by
  coverage_level, driver credit_score, and vehicle age
- Coverage amount strictly tied to vehicle value by policy type
- Deductible set as a realistic fraction (5-10%) of the coverage amount
"""

import random
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from .base_generator import DataGenerator


class PolicyGenerator(DataGenerator):
    """Generate realistic insurance policy data"""

    POLICY_TYPES    = ['COMPREHENSIVE', 'THIRD_PARTY', 'COLLISION', 'LIABILITY']
    COVERAGE_LEVELS = ['BASIC', 'STANDARD', 'PREMIUM']
    STATUSES        = ['ACTIVE', 'EXPIRED', 'CANCELLED', 'SUSPENDED', 'PENDING']
    CURRENCIES      = [('USD', 0.80), ('ZWG', 0.20)]

    # Coverage amount multiplier relative to vehicle market value, by policy type
    COVERAGE_VALUE_MULTIPLIERS = {
        'COMPREHENSIVE': Decimal('1.50'),
        'COLLISION':     Decimal('1.20'),
        'THIRD_PARTY':   Decimal('1.00'),
        'LIABILITY':     Decimal('1.00'),
    }

    # Base premium rate as a fraction of vehicle market value (annual)
    BASE_RATE_RANGE = (0.03, 0.08)    # 3 %  –  8 %

    # Coverage-level loading on the base rate
    COVERAGE_LEVEL_MULTIPLIERS = {
        'BASIC':    1.0,
        'STANDARD': 1.3,
        'PREMIUM':  1.6,
    }

    # Deductible expressed as a fraction of coverage_amount
    DEDUCTIBLE_FRACTION = {
        'BASIC':    (0.08, 0.10),   # 8 – 10 %
        'STANDARD': (0.06, 0.08),   # 6 – 8 %
        'PREMIUM':  (0.04, 0.06),   # 4 – 6 %
    }

    # -----------------------------------------------------------------------
    # Premium calculation
    # -----------------------------------------------------------------------
    @staticmethod
    def calculate_premium(policyholder: dict, vehicle: dict,
                           policy_type: str, coverage_level: str) -> Decimal:
        """
        Realistic premium = base_rate × market_value × coverage_mult
                           × credit_factor × vehicle_age_factor
                           × safety_discount × modification_factor
                           × loyalty_discount

        Base rate: 3-8% of vehicle market_value (annual).
        """
        market_value = float(vehicle['market_value'])
        base_rate    = random.uniform(*PolicyGenerator.BASE_RATE_RANGE)
        base_premium = market_value * base_rate

        # -- Coverage level loading --
        coverage_mult = PolicyGenerator.COVERAGE_LEVEL_MULTIPLIERS[coverage_level]

        # -- Credit score discount (high score = lower risk = lower premium) --
        credit_score = policyholder['credit_score']
        if credit_score >= 750:
            credit_factor = 0.85
        elif credit_score >= 650:
            credit_factor = 0.92
        elif credit_score >= 550:
            credit_factor = 1.00
        else:
            credit_factor = 1.15

        # -- Driver age surcharge (young < 25, senior > 65) --
        age = (datetime.now().date() - policyholder['date_of_birth']).days // 365
        if age < 25:
            age_factor = 1.50
        elif age < 30:
            age_factor = 1.20
        elif age > 65:
            age_factor = 1.10
        else:
            age_factor = 1.00

        # -- Vehicle age factor: new cars have higher replacement cost;
        #    very old cars have higher mechanical risk --
        # Uses manufacture_year (renamed from year)
        vehicle_age = datetime.now().year - vehicle['manufacture_year']
        if vehicle_age < 3:
            vehicle_age_factor = 1.10
        elif vehicle_age > 15:
            vehicle_age_factor = 1.15
        else:
            vehicle_age_factor = 1.00

        # -- Safety feature discounts --
        safety_discount = 1.0
        if vehicle['has_anti_theft']:
            safety_discount -= 0.05
        if vehicle['has_airbags']:
            safety_discount -= 0.03
        if vehicle['has_abs']:
            safety_discount -= 0.02

        # -- Modification surcharge --
        modification_factor = 1.20 if vehicle['is_modified'] else 1.00

        # -- Loyalty discount (capped at 30%) --
        loyalty_discount = max(0.70, 1.0 - policyholder['years_with_company'] * 0.02)

        # -- Defensive licence discount --
        defensive_discount = 0.95 if policyholder.get('has_defensive_license') else 1.00

        premium = (
            base_premium
            * coverage_mult
            * credit_factor
            * age_factor
            * vehicle_age_factor
            * safety_discount
            * modification_factor
            * loyalty_discount
            * defensive_discount
        )

        return Decimal(str(premium)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    # -----------------------------------------------------------------------
    # Single-policy generation
    # -----------------------------------------------------------------------
    @staticmethod
    def generate_policy(policyholder: dict, vehicle: dict, index: int) -> dict:
        """Generate a single insurance policy"""

        # Policy type (weighted — comprehensive most common in Zimbabwe)
        policy_type = PolicyGenerator.weighted_choice(
            PolicyGenerator.POLICY_TYPES,
            [0.50, 0.20, 0.20, 0.10]
        )

        # Coverage level (weighted)
        coverage_level = PolicyGenerator.weighted_choice(
            PolicyGenerator.COVERAGE_LEVELS,
            [0.30, 0.50, 0.20]
        )

        # Currency — 80% USD, 20% ZWG
        currency = PolicyGenerator.weighted_choice(
            ['USD', 'ZWG'], [0.80, 0.20]
        )

        # Realistic premium
        premium_amount = PolicyGenerator.calculate_premium(
            policyholder, vehicle, policy_type, coverage_level
        )

        # Coverage amount — strictly tied to vehicle value
        vehicle_value    = vehicle['market_value']
        coverage_mult    = PolicyGenerator.COVERAGE_VALUE_MULTIPLIERS[policy_type]
        coverage_amount  = (vehicle_value * coverage_mult).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )

        # Deductible — realistic fraction of coverage_amount
        ded_low, ded_high = PolicyGenerator.DEDUCTIBLE_FRACTION[coverage_level]
        deductible_fraction = random.uniform(ded_low, ded_high)
        deductible = (
            coverage_amount * Decimal(str(round(deductible_fraction, 4)))
        ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Policy dates
        days_ago   = random.randint(0, 730)
        start_date = datetime.now().date() - timedelta(days=days_ago)
        end_date   = start_date + timedelta(days=365)

        # Status based on dates
        today = datetime.now().date()
        if end_date < today:
            status = PolicyGenerator.weighted_choice(
                ['EXPIRED', 'CANCELLED'], [0.70, 0.30]
            )
        elif start_date > today:
            status = 'PENDING'
        else:
            status = PolicyGenerator.weighted_choice(
                ['ACTIVE', 'SUSPENDED', 'CANCELLED'], [0.85, 0.05, 0.10]
            )

        # Add-on coverages (more likely at premium tier)
        if coverage_level == 'PREMIUM':
            has_roadside_assistance = random.random() > 0.30
            has_rental_coverage     = random.random() > 0.40
            has_glass_coverage      = random.random() > 0.50
        elif coverage_level == 'STANDARD':
            has_roadside_assistance = random.random() > 0.60
            has_rental_coverage     = random.random() > 0.70
            has_glass_coverage      = random.random() > 0.80
        else:
            has_roadside_assistance = random.random() > 0.80
            has_rental_coverage     = random.random() > 0.90
            has_glass_coverage      = random.random() > 0.90

        policy = {
            'policy_number':          PolicyGenerator.generate_id('POL', 12),
            'policyholder_id':        policyholder['policy_holder_id'],
            # vehicle referenced by VIN (natural unique key — no more vehicle_id)
            'vehicle_vin':            vehicle['vin'],
            'policy_type':            policy_type,
            'coverage_level':         coverage_level,
            'currency':               currency,
            'status':                 status,
            'premium_amount':         premium_amount,
            'coverage_amount':        coverage_amount,
            'deductible':             deductible,
            'start_date':             start_date,
            'end_date':               end_date,
            'has_roadside_assistance': has_roadside_assistance,
            'has_rental_coverage':    has_rental_coverage,
            'has_glass_coverage':     has_glass_coverage,
        }

        return policy

    # -----------------------------------------------------------------------
    # Batch generation
    # -----------------------------------------------------------------------
    @staticmethod
    def generate_batch(policyholders: list, vehicles: list) -> list:
        """Generate one policy per vehicle"""
        print(f"Generating policies for {len(vehicles)} vehicles...")

        policyholder_dict = {
            ph['policy_holder_id']: ph for ph in policyholders
        }

        policies = []
        for i, vehicle in enumerate(vehicles):
            policyholder = policyholder_dict[vehicle['policyholder_id']]
            policy       = PolicyGenerator.generate_policy(policyholder, vehicle, i)
            policies.append(policy)

            if (i + 1) % 100 == 0:
                print(f"  Generated {i + 1}/{len(vehicles)} policies")

        print(f"✓ Generated {len(policies)} policies")
        return policies