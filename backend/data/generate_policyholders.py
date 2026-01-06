"""
Generate synthetic policyholder data
"""

import random
from datetime import datetime, timedelta
from decimal import Decimal
from .base_generator import DataGenerator, InsuranceDataConfig, fake


class PolicyholderGenerator(DataGenerator):
    """Generate realistic policyholder data"""
    
    @staticmethod
    def generate_policyholder(index):
        """Generate a single policyholder"""
        
        # Generate basic demographics
        gender = random.choice(['M', 'F'])
        first_name = fake.first_name_male() if gender == 'M' else fake.first_name_female()
        last_name = fake.last_name()
        
        # Generate age between 18 and 80
        age = random.randint(18, 80)
        date_of_birth = datetime.now().date() - timedelta(days=age * 365 + random.randint(0, 364))
        
        # Marital status (weighted by age)
        if age < 25:
            marital_status = PolicyholderGenerator.weighted_choice(
                ['SINGLE', 'MARRIED', 'DIVORCED'],
                [0.8, 0.15, 0.05]
            )
        elif age < 40:
            marital_status = PolicyholderGenerator.weighted_choice(
                ['SINGLE', 'MARRIED', 'DIVORCED'],
                [0.3, 0.6, 0.1]
            )
        else:
            marital_status = PolicyholderGenerator.weighted_choice(
                ['SINGLE', 'MARRIED', 'DIVORCED', 'WIDOWED'],
                [0.15, 0.6, 0.2, 0.05]
            )
        
        # Occupation based on age
        if age < 22:
            occupation = 'STUDENT'
        elif age > 65:
            occupation = PolicyholderGenerator.weighted_choice(
                ['RETIRED', 'EMPLOYED', 'SELF_EMPLOYED'],
                [0.7, 0.2, 0.1]
            )
        else:
            occupation = PolicyholderGenerator.weighted_choice(
                ['EMPLOYED', 'SELF_EMPLOYED', 'UNEMPLOYED'],
                [0.75, 0.2, 0.05]
            )
        
        # Generate income based on occupation
        income_range = InsuranceDataConfig.OCCUPATIONS[occupation]['income_range']
        annual_income = Decimal(random.uniform(income_range[0], income_range[1]))
        
        # Credit score (normally distributed around 680)
        credit_score = int(random.gauss(680, 80))
        credit_score = max(300, min(850, credit_score))
        
        # Years with company (weighted towards newer customers)
        years_with_company = PolicyholderGenerator.weighted_choice(
            list(range(0, 21)),
            [15, 12, 10, 8, 7, 6, 5, 4, 3, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        )
        
        # Address information
        state = random.choice(InsuranceDataConfig.US_STATES)
        
        policyholder = {
            'policy_holder_id': PolicyholderGenerator.generate_id('PH', 10),
            'first_name': first_name,
            'last_name': last_name,
            'date_of_birth': date_of_birth,
            'gender': gender,
            'email': f"{first_name.lower()}.{last_name.lower()}.{random.randint(1, 999)}@email.com",
            'phone_number': fake.phone_number()[:15],
            'address_line1': fake.street_address(),
            'address_line2': fake.secondary_address() if random.random() > 0.7 else '',
            'city': fake.city(),
            'state': state,
            'postal_code': fake.zipcode(),
            'country': 'USA',
            'marital_status': marital_status,
            'occupation': occupation,
            'annual_income': annual_income,
            'credit_score': credit_score,
            'years_with_company': years_with_company,
            'is_active': random.random() > 0.05,  # 95% active
        }
        
        return policyholder
    
    @staticmethod
    def generate_batch(count=1000):
        """Generate multiple policyholders"""
        print(f"Generating {count} policyholders...")
        policyholders = []
        
        for i in range(count):
            policyholder = PolicyholderGenerator.generate_policyholder(i)
            policyholders.append(policyholder)
            
            if (i + 1) % 100 == 0:
                print(f"  Generated {i + 1}/{count} policyholders")
        
        print(f"✓ Generated {len(policyholders)} policyholders")
        return policyholders