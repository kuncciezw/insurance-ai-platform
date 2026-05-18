"""
Generate synthetic policyholder data - Zimbabwe Market
REFACTORED VERSION
- Removed postal_code
- Added has_driving_license, has_defensive_license, is_medical_license_valid
- Explicit annual_income = monthly_income * 12
- Simulated credit score algorithm (not random lookup)
- Credit rating derived strictly from computed score
"""

import random
from datetime import datetime, timedelta
from decimal import Decimal
from .base_generator import DataGenerator, InsuranceDataConfig, fake


class PolicyholderGenerator(DataGenerator):
    """Generate realistic Zimbabwe policyholder data"""

    # -----------------------------------------------------------------------
    # Credit score simulation
    # -----------------------------------------------------------------------
    @staticmethod
    def _compute_credit_score(annual_income: float, age: int,
                               occupation: str, has_defensive_license: bool) -> int:
        """
        Simulate a Zimbabwe-context credit score.

        Base: 550
        +50  if annual_income > $30,000 USD
        +50  if annual_income > $60,000 USD  (stacks with the above)
        +40  if age > 25
        +60  if occupation in EMPLOYED / SELF_EMPLOYED
        +30  if has_defensive_driving licence
        Capped between 300 and 850.
        """
        score = 550

        if float(annual_income) > 30_000:
            score += 50
        if float(annual_income) > 60_000:
            score += 50          # cumulative — high earner gets both boosts

        if age > 25:
            score += 40

        if occupation in ('EMPLOYED', 'SELF_EMPLOYED'):
            score += 60

        if has_defensive_license:
            score += 30

        return max(300, min(850, score))

    @staticmethod
    def _credit_rating_from_score(score: int) -> str:
        """Derive the qualitative credit rating from the numeric score."""
        if score >= 750:
            return 'EXCELLENT'
        elif score >= 650:
            return 'GOOD'
        elif score >= 550:
            return 'FAIR'
        else:
            return 'POOR'

    # -----------------------------------------------------------------------
    # Single-policyholder generation
    # -----------------------------------------------------------------------
    @staticmethod
    def generate_policyholder(index):
        """Generate a single Zimbabwe-based policyholder"""

        # Demographics
        gender = random.choice(['M', 'F'])

        name_type = PolicyholderGenerator.weighted_choice(
            ['SHONA', 'NDEBELE', 'OTHER'],
            [0.7, 0.2, 0.1]
        )
        if name_type == 'SHONA':
            last_name = random.choice(InsuranceDataConfig.SHONA_SURNAMES)
        elif name_type == 'NDEBELE':
            last_name = random.choice(InsuranceDataConfig.NDEBELE_SURNAMES)
        else:
            last_name = fake.last_name()

        first_name = random.choice(
            InsuranceDataConfig.FIRST_NAMES['MALE' if gender == 'M' else 'FEMALE']
        )

        # Age & date of birth
        age = random.randint(18, 80)
        date_of_birth = (
            datetime.now().date() - timedelta(days=age * 365 + random.randint(0, 364))
        )

        # Marital status (weighted by age)
        if age < 25:
            marital_status = PolicyholderGenerator.weighted_choice(
                ['SINGLE', 'MARRIED', 'DIVORCED'], [0.80, 0.15, 0.05]
            )
        elif age < 40:
            marital_status = PolicyholderGenerator.weighted_choice(
                ['SINGLE', 'MARRIED', 'DIVORCED'], [0.30, 0.60, 0.10]
            )
        else:
            marital_status = PolicyholderGenerator.weighted_choice(
                ['SINGLE', 'MARRIED', 'DIVORCED', 'WIDOWED'], [0.15, 0.60, 0.20, 0.05]
            )

        # Occupation (weighted by age)
        if age < 22:
            occupation = 'STUDENT'
        elif age > 65:
            occupation = PolicyholderGenerator.weighted_choice(
                ['RETIRED', 'EMPLOYED', 'SELF_EMPLOYED'], [0.70, 0.20, 0.10]
            )
        else:
            occupation = PolicyholderGenerator.weighted_choice(
                ['EMPLOYED', 'SELF_EMPLOYED', 'UNEMPLOYED'], [0.65, 0.25, 0.10]
            )

        # Income
        income_range   = InsuranceDataConfig.OCCUPATIONS[occupation]['income_range']
        monthly_income = Decimal(str(round(random.uniform(*income_range), 2)))
        annual_income  = monthly_income * 12           # explicitly calculated

        # ----------------------------------------------------------------
        # Licence booleans
        # ----------------------------------------------------------------
        has_driving_license     = random.random() < 0.95   # 95% have a driving licence
        has_defensive_license   = random.random() < 0.15   # 15% have defensive driving cert
        is_medical_license_valid = random.random() < 0.98  # 98% medically fit to drive

        # ----------------------------------------------------------------
        # Credit score — computed from financial signals, not random lookup
        # ----------------------------------------------------------------
        credit_score  = PolicyholderGenerator._compute_credit_score(
            annual_income=float(annual_income),
            age=age,
            occupation=occupation,
            has_defensive_license=has_defensive_license,
        )
        credit_rating = PolicyholderGenerator._credit_rating_from_score(credit_score)

        # Years with company
        years_with_company = PolicyholderGenerator.weighted_choice(
            list(range(0, 21)),
            [15, 12, 10, 8, 7, 6, 5, 4, 3, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        )

        # Zimbabwe location
        province = random.choice(list(InsuranceDataConfig.PROVINCES.keys()))
        city     = random.choice(InsuranceDataConfig.PROVINCES[province])

        # Contact details
        national_id   = PolicyholderGenerator.generate_zim_national_id()
        mobile_number = PolicyholderGenerator.generate_zim_mobile()

        email_domain = random.choice(['gmail.com', 'yahoo.com', 'outlook.com', 'mail.com'])
        email        = (
            f"{first_name.lower()}.{last_name.lower()}"
            f"{random.randint(1, 999)}@{email_domain}"
        )

        address_line1 = fake.street_address()

        policyholder = {
            'policy_holder_id':       PolicyholderGenerator.generate_id('ZW-PH', 10),
            'national_id':            national_id,
            'first_name':             first_name,
            'last_name':              last_name,
            'date_of_birth':          date_of_birth,
            'gender':                 gender,
            'email':                  email,
            'phone_number':           mobile_number,
            'address_line1':          address_line1,
            'address_line2':          fake.secondary_address() if random.random() > 0.85 else '',
            'city':                   city,
            'state':                  province,   # field name kept for model compat
            # postal_code intentionally omitted (field dropped from schema)
            'country':                'Zimbabwe',
            'marital_status':         marital_status,
            'occupation':             occupation,
            'monthly_income':         monthly_income,
            'annual_income':          annual_income,          # explicit, not model-computed
            'credit_rating':          credit_rating,          # derived from score
            'credit_score':           credit_score,           # simulated algorithm
            'years_with_company':     years_with_company,
            'has_driving_license':    has_driving_license,
            'has_defensive_license':  has_defensive_license,
            'is_medical_license_valid': is_medical_license_valid,
            'is_active':              random.random() > 0.05,
        }

        return policyholder

    # -----------------------------------------------------------------------
    # Batch generation
    # -----------------------------------------------------------------------
    @staticmethod
    def generate_batch(count=1000):
        """Generate multiple Zimbabwe policyholders"""
        print(f"Generating {count} Zimbabwe policyholders...")
        policyholders = []

        for i in range(count):
            policyholders.append(PolicyholderGenerator.generate_policyholder(i))

            if (i + 1) % 100 == 0:
                print(f"  Generated {i + 1}/{count} policyholders")

        print(f"✓ Generated {len(policyholders)} policyholders")
        return policyholders