"""
Generate synthetic policyholder data - Zimbabwe Market
"""

import random
from datetime import datetime, timedelta
from decimal import Decimal
from .base_generator import DataGenerator, InsuranceDataConfig, fake


class PolicyholderGenerator(DataGenerator):
    """Generate realistic Zimbabwe policyholder data"""
    
    @staticmethod
    def generate_policyholder(index):
        """Generate a single Zimbabwe-based policyholder"""
        
        # Generate demographics with Zimbabwe names
        gender = random.choice(['M', 'F'])
        
        # 70% Shona, 20% Ndebele, 10% Other (English names)
        name_type = PolicyholderGenerator.weighted_choice(
            ['SHONA', 'NDEBELE', 'OTHER'],
            [0.7, 0.2, 0.1]
        )
        
        if name_type == 'SHONA':
            last_name = random.choice(InsuranceDataConfig.SHONA_SURNAMES)
        elif name_type == 'NDEBELE':
            last_name = random.choice(InsuranceDataConfig.NDEBELE_SURNAMES)
        else:
            last_name = fake.last_name()  # English surname
        
        first_name = random.choice(
            InsuranceDataConfig.FIRST_NAMES['MALE'] if gender == 'M' 
            else InsuranceDataConfig.FIRST_NAMES['FEMALE']
        )
        
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
                [0.65, 0.25, 0.10]  # Higher self-employment rate in Zimbabwe
            )
        
        # Generate monthly income (Zimbabwe uses USD)
        income_range = InsuranceDataConfig.OCCUPATIONS[occupation]['income_range']
        monthly_income = Decimal(random.uniform(income_range[0], income_range[1]))
        annual_income = monthly_income * 12
        
        # Credit rating (qualitative) - Zimbabwe doesn't have FICO
        credit_rating = PolicyholderGenerator.weighted_choice(
            list(InsuranceDataConfig.CREDIT_RATINGS.keys()),
            [0.15, 0.35, 0.30, 0.15, 0.05]  # Weights for each rating
        )
        
        # Convert to numeric score for ML models (internal use only)
        rating_range = InsuranceDataConfig.CREDIT_RATINGS[credit_rating]
        credit_score = random.randint(rating_range[0], rating_range[1])
        
        # Years with company (weighted towards newer customers)
        years_with_company = PolicyholderGenerator.weighted_choice(
            list(range(0, 21)),
            [15, 12, 10, 8, 7, 6, 5, 4, 3, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        )
        
        # Zimbabwe location
        province = random.choice(list(InsuranceDataConfig.PROVINCES.keys()))
        city = random.choice(InsuranceDataConfig.PROVINCES[province])
        
        # Generate Zimbabwe-specific contact details
        national_id = PolicyholderGenerator.generate_zim_national_id()
        mobile_number = PolicyholderGenerator.generate_zim_mobile()
        
        # Email address
        email_domain = random.choice(['gmail.com', 'yahoo.com', 'outlook.com', 'mail.com'])
        email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}@{email_domain}"
        
        # Address
        address_line1 = fake.street_address()
        
        # Postal code (Zimbabwe format - not all areas have them)
        if city in ['Harare', 'Bulawayo']:
            postal_code = f"{'H' if city == 'Harare' else 'B'}{random.randint(1000, 9999)}"
        else:
            postal_code = ''  # Many areas don't have postal codes
        
        policyholder = {
            'policy_holder_id': PolicyholderGenerator.generate_id('ZW-PH', 10),
            'national_id': national_id,
            'first_name': first_name,
            'last_name': last_name,
            'date_of_birth': date_of_birth,
            'gender': gender,
            'email': email,
            'phone_number': mobile_number,
            'address_line1': address_line1,
            'address_line2': fake.secondary_address() if random.random() > 0.85 else '',
            'city': city,
            'state': province,  # Keep field name 'state' for compatibility, but it's province
            'postal_code': postal_code,
            'country': 'Zimbabwe',
            'marital_status': marital_status,
            'occupation': occupation,
            'monthly_income': monthly_income,
            'annual_income': annual_income,
            'credit_rating': credit_rating,  # Qualitative
            'credit_score': credit_score,     # Numeric (for ML models)
            'years_with_company': years_with_company,
            'is_active': random.random() > 0.05,  # 95% active
        }
        
        return policyholder
    
    @staticmethod
    def generate_batch(count=1000):
        """Generate multiple Zimbabwe policyholders"""
        print(f"Generating {count} Zimbabwe policyholders...")
        policyholders = []
        
        for i in range(count):
            policyholder = PolicyholderGenerator.generate_policyholder(i)
            policyholders.append(policyholder)
            
            if (i + 1) % 100 == 0:
                print(f"  Generated {i + 1}/{count} policyholders")
        
        print(f"✓ Generated {len(policyholders)} policyholders")
        return policyholders