"""
Generate synthetic insurance policy data
"""

import random
from datetime import datetime, timedelta
from decimal import Decimal
from .base_generator import DataGenerator


class PolicyGenerator(DataGenerator):
    """Generate realistic insurance policy data"""
    
    POLICY_TYPES = ['COMPREHENSIVE', 'THIRD_PARTY', 'COLLISION', 'LIABILITY']
    COVERAGE_LEVELS = ['BASIC', 'STANDARD', 'PREMIUM']
    STATUSES = ['ACTIVE', 'EXPIRED', 'CANCELLED', 'SUSPENDED', 'PENDING']
    
    # Base premium rates by policy type (annual)
    BASE_PREMIUMS = {
        'COMPREHENSIVE': (1200, 3500),
        'THIRD_PARTY': (400, 1000),
        'COLLISION': (800, 2000),
        'LIABILITY': (500, 1200)
    }
    
    # Coverage multipliers by level
    COVERAGE_MULTIPLIERS = {
        'BASIC': 1.0,
        'STANDARD': 1.5,
        'PREMIUM': 2.5
    }
    
    @staticmethod
    def calculate_premium(policyholder, vehicle, policy_type, coverage_level):
        """Calculate premium based on risk factors"""
        
        # Base premium for policy type
        base_range = PolicyGenerator.BASE_PREMIUMS[policy_type]
        base_premium = random.uniform(base_range[0], base_range[1])
        
        # Age factor (younger and older drivers pay more)
        age = (datetime.now().date() - policyholder['date_of_birth']).days // 365
        if age < 25:
            age_factor = 1.5
        elif age < 30:
            age_factor = 1.2
        elif age > 65:
            age_factor = 1.1
        else:
            age_factor = 1.0
        
        # Credit score factor
        credit_score = policyholder['credit_score']
        if credit_score < 600:
            credit_factor = 1.4
        elif credit_score < 650:
            credit_factor = 1.2
        elif credit_score < 700:
            credit_factor = 1.1
        else:
            credit_factor = 1.0
        
        # Vehicle value factor
        vehicle_value = float(vehicle['market_value'])
        if vehicle_value > 60000:
            value_factor = 1.3
        elif vehicle_value > 40000:
            value_factor = 1.15
        else:
            value_factor = 1.0
        
        # Vehicle age factor (very new or very old are riskier)
        vehicle_age = datetime.now().year - vehicle['year']
        if vehicle_age < 2:
            vehicle_age_factor = 1.1
        elif vehicle_age > 10:
            vehicle_age_factor = 1.2
        else:
            vehicle_age_factor = 1.0
        
        # Safety features discount
        safety_discount = 1.0
        if vehicle['has_anti_theft']:
            safety_discount -= 0.05
        if vehicle['has_airbags']:
            safety_discount -= 0.03
        if vehicle['has_abs']:
            safety_discount -= 0.02
        
        # Modification penalty
        modification_factor = 1.2 if vehicle['is_modified'] else 1.0
        
        # Experience discount
        years_discount = max(0.7, 1.0 - (policyholder['years_with_company'] * 0.02))
        
        # Coverage level multiplier
        coverage_multiplier = PolicyGenerator.COVERAGE_MULTIPLIERS[coverage_level]
        
        # Calculate final premium
        premium = (
            base_premium *
            age_factor *
            credit_factor *
            value_factor *
            vehicle_age_factor *
            safety_discount *
            modification_factor *
            years_discount *
            coverage_multiplier
        )
        
        return Decimal(premium).quantize(Decimal('0.01'))
    
    @staticmethod
    def generate_policy(policyholder, vehicle, index):
        """Generate a single insurance policy"""
        
        # Policy type (weighted)
        policy_type = PolicyGenerator.weighted_choice(
            PolicyGenerator.POLICY_TYPES,
            [0.5, 0.2, 0.2, 0.1]
        )
        
        # Coverage level (weighted)
        coverage_level = PolicyGenerator.weighted_choice(
            PolicyGenerator.COVERAGE_LEVELS,
            [0.3, 0.5, 0.2]
        )
        
        # Calculate premium
        premium_amount = PolicyGenerator.calculate_premium(
            policyholder, vehicle, policy_type, coverage_level
        )
        
        # Coverage amount (based on vehicle value and policy type)
        vehicle_value = vehicle['market_value']
        if policy_type == 'COMPREHENSIVE':
            coverage_amount = vehicle_value * Decimal('1.5')
        elif policy_type == 'COLLISION':
            coverage_amount = vehicle_value * Decimal('1.2')
        else:
            coverage_amount = vehicle_value
        
        # Deductible (inversely proportional to premium)
        if coverage_level == 'BASIC':
            deductible = Decimal(random.choice([500, 1000, 1500]))
        elif coverage_level == 'STANDARD':
            deductible = Decimal(random.choice([250, 500, 750]))
        else:
            deductible = Decimal(random.choice([100, 250, 500]))
        
        # Policy dates
        # Some policies started in the past, some are recent
        days_ago = random.randint(0, 730)  # Up to 2 years ago
        start_date = datetime.now().date() - timedelta(days=days_ago)
        end_date = start_date + timedelta(days=365)
        
        # Policy status (based on dates)
        today = datetime.now().date()
        if end_date < today:
            status = PolicyGenerator.weighted_choice(
                ['EXPIRED', 'CANCELLED'],
                [0.7, 0.3]
            )
        elif start_date > today:
            status = 'PENDING'
        else:
            status = PolicyGenerator.weighted_choice(
                ['ACTIVE', 'SUSPENDED', 'CANCELLED'],
                [0.85, 0.05, 0.1]
            )
        
        # Additional coverage options (more likely with premium)
        if coverage_level == 'PREMIUM':
            has_roadside_assistance = random.random() > 0.3
            has_rental_coverage = random.random() > 0.4
            has_glass_coverage = random.random() > 0.5
        elif coverage_level == 'STANDARD':
            has_roadside_assistance = random.random() > 0.6
            has_rental_coverage = random.random() > 0.7
            has_glass_coverage = random.random() > 0.8
        else:
            has_roadside_assistance = random.random() > 0.8
            has_rental_coverage = random.random() > 0.9
            has_glass_coverage = random.random() > 0.9
        
        policy = {
            'policy_number': PolicyGenerator.generate_id('POL', 12),
            'policyholder_id': policyholder['policy_holder_id'],
            'vehicle_id': vehicle['vehicle_id'],
            'policy_type': policy_type,
            'coverage_level': coverage_level,
            'status': status,
            'premium_amount': premium_amount,
            'coverage_amount': coverage_amount,
            'deductible': deductible,
            'start_date': start_date,
            'end_date': end_date,
            'has_roadside_assistance': has_roadside_assistance,
            'has_rental_coverage': has_rental_coverage,
            'has_glass_coverage': has_glass_coverage,
        }
        
        return policy
    
    @staticmethod
    def generate_batch(policyholders, vehicles):
        """Generate policies for vehicles"""
        print(f"Generating policies for {len(vehicles)} vehicles...")
        
        # Create lookup dictionary for policyholders
        policyholder_dict = {
            ph['policy_holder_id']: ph for ph in policyholders
        }
        
        policies = []
        for i, vehicle in enumerate(vehicles):
            policyholder = policyholder_dict[vehicle['policyholder_id']]
            
            policy = PolicyGenerator.generate_policy(policyholder, vehicle, i)
            policies.append(policy)
            
            if (i + 1) % 100 == 0:
                print(f"  Generated {i + 1}/{len(vehicles)} policies")
        
        print(f"✓ Generated {len(policies)} policies")
        return policies