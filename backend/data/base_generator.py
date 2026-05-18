"""
Base data generator utilities - Zimbabwe Market Configuration
"""

import random
import string
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)


class DataGenerator:
    """Base class for data generation utilities"""

    @staticmethod
    def generate_id(prefix, length=8):
        """Generate unique ID with prefix"""
        random_part = ''.join(random.choices(string.digits, k=length))
        return f"{prefix}-{random_part}"

    @staticmethod
    def generate_vin():
        """Generate realistic VIN (Vehicle Identification Number)"""
        valid_chars = 'ABCDEFGHJKLMNPRSTUVWXYZ0123456789'
        return ''.join(random.choices(valid_chars, k=17))

    @staticmethod
    def generate_zim_number_plate():
        """Generate Zimbabwe number plate format: AAA 1234"""
        letters  = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=3))
        numbers  = ''.join(random.choices('0123456789', k=4))
        return f"{letters} {numbers}"

    @staticmethod
    def generate_zim_national_id():
        """Generate Zimbabwe National ID format: 63-123456A12"""
        year    = random.randint(50, 99)
        numbers = ''.join(random.choices('0123456789', k=6))
        letter  = random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
        check   = ''.join(random.choices('0123456789', k=2))
        return f"{year}-{numbers}{letter}{check}"

    @staticmethod
    def generate_zim_mobile():
        """Generate Zimbabwe mobile number"""
        prefix = random.choice(['71', '77', '78', '73'])
        number = ''.join(random.choices('0123456789', k=7))
        return f"+263{prefix}{number}"

    @staticmethod
    def random_date_between(start_date, end_date):
        """Generate random date between two dates"""
        time_between = end_date - start_date
        random_days  = random.randrange(max(time_between.days, 1))
        return start_date + timedelta(days=random_days)

    @staticmethod
    def random_datetime_between(start_datetime, end_datetime):
        """Generate random datetime between two datetimes"""
        if start_datetime >= end_datetime:
            return start_datetime
        seconds_between = int((end_datetime - start_datetime).total_seconds())
        if seconds_between <= 0:
            return start_datetime
        random_seconds = random.randrange(seconds_between)
        return start_datetime + timedelta(seconds=random_seconds)

    @staticmethod
    def weighted_choice(choices, weights):
        """Make weighted random choice"""
        return random.choices(choices, weights=weights, k=1)[0]

    @staticmethod
    def round_to_decimal(value, decimals=2):
        """Round float to specified decimal places"""
        return round(float(value), decimals)


class InsuranceDataConfig:
    """Configuration constants for Zimbabwe insurance market"""

    # Zimbabwe Provinces and Major Cities
    PROVINCES = {
        'HARARE':               ['Harare', 'Chitungwiza', 'Epworth', 'Norton', 'Ruwa'],
        'BULAWAYO':             ['Bulawayo'],
        'MANICALAND':           ['Mutare', 'Rusape', 'Chimanimani', 'Chipinge'],
        'MIDLANDS':             ['Gweru', 'Kwekwe', 'Shurugwi', 'Gokwe'],
        'MASVINGO':             ['Masvingo', 'Chiredzi', 'Triangle'],
        'MASHONALAND_EAST':     ['Marondera', 'Ruwa', 'Macheke'],
        'MASHONALAND_WEST':     ['Chinhoyi', 'Kariba', 'Makuti'],
        'MASHONALAND_CENTRAL':  ['Bindura', 'Shamva', 'Mount Darwin'],
        'MATABELELAND_NORTH':   ['Victoria Falls', 'Hwange', 'Binga'],
        'MATABELELAND_SOUTH':   ['Gwanda', 'Beitbridge', 'Plumtree'],
    }

    # Common Zimbabwean Shona Surnames
    SHONA_SURNAMES = [
        'Moyo', 'Ncube', 'Dube', 'Sibanda', 'Ndlovu', 'Mpofu', 'Khumalo',
        'Nyathi', 'Madziva', 'Chikwanha', 'Mapfumo', 'Mudzingwa', 'Chiduku',
        'Mutasa', 'Gumbo', 'Muromo', 'Mushonga', 'Chipanga', 'Marowa',
        'Mavhima', 'Chimombe', 'Mlambo', 'Nkomo', 'Phiri', 'Banda',
        'Tshuma', 'Mpofu', 'Zhou', 'Chikwava', 'Magura', 'Rusere',
        'Makoni', 'Mutamangira', 'Shumba', 'Mhuru', 'Gwaze', 'Biti',
        'Macheka', 'Chihuri', 'Mawere', 'Takaendesa', 'Chipunza', 'Matanga',
    ]

    # Common Zimbabwean Ndebele Surnames
    NDEBELE_SURNAMES = [
        'Ncube', 'Dube', 'Sibanda', 'Ndlovu', 'Mpofu', 'Khumalo', 'Moyo',
        'Nyathi', 'Nkomo', 'Tshuma', 'Mhlanga', 'Mlilo', 'Nyoni', 'Nkala',
        'Gumede', 'Hadebe', 'Ngwenya', 'Mazibuko', 'Mkhize', 'Zungu',
    ]

    # Common Zimbabwean First Names (Mixed - Shona/Ndebele/English)
    FIRST_NAMES = {
        'MALE': [
            'Tendai', 'Tapiwa', 'Tinashe', 'Tatenda', 'Tawanda', 'Takudzwa',
            'Munyaradzi', 'Panashe', 'Tanaka', 'Anesu', 'Tinotenda', 'Tafadzwa',
            'Nkululeko', 'Siyabonga', 'Lungile', 'Khulekani', 'Mandla', 'Thabo',
            'Brian', 'Michael', 'David', 'Peter', 'John', 'James', 'Andrew',
            'Christopher', 'Richard', 'Thomas', 'Daniel', 'Joseph',
        ],
        'FEMALE': [
            'Rudo', 'Chiedza', 'Tsitsi', 'Rumbidzai', 'Tariro', 'Nyasha',
            'Ropafadzo', 'Chenai', 'Rutendo', 'Memory', 'Tendai', 'Yeukai',
            'Nothando', 'Nobuhle', 'Siphiwe', 'Zanele', 'Thandi', 'Lindiwe',
            'Sandra', 'Patricia', 'Elizabeth', 'Mary', 'Grace', 'Faith',
            'Sharon', 'Michelle', 'Angela', 'Christine', 'Sarah', 'Rachel',
        ],
    }

    # Vehicles common in Zimbabwe market
    VEHICLES = {
        'Toyota': {
            'models': ['Corolla', 'Hilux', 'Land Cruiser', 'Fortuner', 'Vitz',
                       'Wish', 'Prado', 'RunX', 'Yaris', 'Raum'],
            'base_value': (6000, 65000),
            'type': 'SEDAN',
        },
        'Nissan': {
            'models': ['X-Trail', 'March', 'Navara', 'Patrol', 'Note',
                       'Qashqai', 'Juke', 'Hardbody', 'NP300'],
            'base_value': (5000, 50000),
            'type': 'SEDAN',
        },
        'Honda': {
            'models': ['Fit', 'CR-V', 'Accord', 'Civic', 'Stream', 'HR-V'],
            'base_value': (5500, 40000),
            'type': 'SEDAN',
        },
        'Mazda': {
            'models': ['Demio', 'Axela', 'CX-5', 'BT-50', 'Atenza', 'Premacy'],
            'base_value': (4500, 38000),
            'type': 'SEDAN',
        },
        'Isuzu': {
            'models': ['D-Max', 'KB', 'MU-X', 'Trooper'],
            'base_value': (12000, 55000),
            'type': 'TRUCK',
        },
        'Mercedes-Benz': {
            'models': ['C-Class', 'E-Class', 'GLE', 'Sprinter', 'Vito', 'ML-Class'],
            'base_value': (15000, 85000),
            'type': 'SEDAN',
        },
        'BMW': {
            'models': ['3 Series', '5 Series', 'X3', 'X5', '1 Series', 'X1'],
            'base_value': (12000, 75000),
            'type': 'SEDAN',
        },
        'Volkswagen': {
            'models': ['Polo', 'Golf', 'Amarok', 'Tiguan', 'Passat'],
            'base_value': (7000, 45000),
            'type': 'SEDAN',
        },
        'Ford': {
            'models': ['Ranger', 'Fiesta', 'Focus', 'EcoSport', 'Everest'],
            'base_value': (8000, 50000),
            'type': 'TRUCK',
        },
        'Mitsubishi': {
            'models': ['Pajero', 'L200', 'ASX', 'Outlander', 'Colt'],
            'base_value': (6000, 45000),
            'type': 'SUV',
        },
        'Suzuki': {
            'models': ['Swift', 'Vitara', 'Jimny', 'Alto', 'Dzire'],
            'base_value': (4000, 25000),
            'type': 'SEDAN',
        },
    }

    # Zimbabwe occupations with realistic income ranges (USD monthly)
    OCCUPATIONS = {
        'EMPLOYED': {
            'titles': [
                'Teacher', 'Nurse', 'Accountant', 'Bank Teller', 'Civil Servant',
                'Sales Representative', 'Administrator', 'IT Officer', 'Pharmacist',
                'Engineer', 'Manager', 'Supervisor', 'Secretary',
            ],
            'income_range': (200, 2500),
        },
        'SELF_EMPLOYED': {
            'titles': [
                'Business Owner', 'Trader', 'Contractor', 'Consultant',
                'Transport Operator', 'Shop Owner', 'Vendor', 'Farmer',
            ],
            'income_range': (150, 5000),
        },
        'RETIRED': {
            'titles': ['Retired'],
            'income_range': (80, 800),
        },
        'STUDENT': {
            'titles': ['Student'],
            'income_range': (0, 300),
        },
        'UNEMPLOYED': {
            'titles': ['Unemployed'],
            'income_range': (0, 50),
        },
    }

    # Zimbabwe incident locations
    INCIDENT_LOCATIONS = [
        'Harare CBD', 'Bulawayo CBD', 'Highway A1', 'Highway A2', 'Highway A5',
        'Chirundu Border Post', 'Beitbridge Border Post', 'Victoria Falls',
        'Shopping Center Parking', 'Residential Area', 'Township Road',
        'Industrial Area', 'Robert Mugabe Road', 'Samora Machel Avenue',
        'Simon Mazorodze Road', 'Bulawayo Road', 'Airport Road',
        'Rural Road', 'Farm Road', 'Main Street', 'Parking Lot',
        'Gas Station', 'Commuter Terminus', 'Tollgate', 'Roadblock',
    ]

    # Credit rating system (internal numeric score for ML models)
    CREDIT_RATINGS = {
        'EXCELLENT':  (750, 850),
        'GOOD':       (650, 749),
        'FAIR':       (550, 649),
        'POOR':       (300, 549),
    }

    # ---------------------------------------------------------------------------
    # Fraud patterns — REFACTORED
    # Removed: no_police_report (field dropped), injury-related patterns
    # Enhanced: financial anomalies, suspicious timing, coverage-limit gaming
    # ---------------------------------------------------------------------------
    FRAUD_PATTERNS = {
        # Core financial anomaly: claimed amount is suspiciously close to
        # the policy coverage_amount (coverage-limit gaming)
        'coverage_limit_gaming': {
            'weight': 0.30,
            'coverage_ratio_range': (0.93, 0.99),   # 93-99% of coverage
            'description': 'Claim amount suspiciously close to coverage limit',
        },

        # Claim inflated beyond what the vehicle's market value would justify
        'amount_inflation': {
            'weight': 0.28,
            'multiplier_range': (1.5, 3.0),          # 1.5× to 3× expected amount
            'description': 'Claimed amount grossly exceeds vehicle market value proportion',
        },

        # Claim filed very shortly after policy inception
        'suspicious_timing': {
            'weight': 0.22,
            'days_after_policy_range': (1, 14),      # Within first 2 weeks
            'description': 'Claim filed within days of policy start',
        },

        # Very high claim on a low-value / heavily depreciated vehicle
        'value_mismatch': {
            'weight': 0.18,
            'min_vehicle_age_years': 8,
            'claim_exceeds_value_by': 1.10,          # Claim > 110% of market value
            'description': 'High claim amount inconsistent with aged vehicle market value',
        },

        # Multiple claims in a short window — tracked across the batch
        'multiple_claims': {
            'weight': 0.15,
            'claims_per_year': (3, 6),
            'description': 'Policyholder has an unusually high claim frequency',
        },

        # Cross-border incidents are harder to verify
        'cross_border_incidents': {
            'weight': 0.18,
            'border_cities': ['Beitbridge', 'Victoria Falls', 'Mutare', 'Chirundu'],
            'description': 'Incident occurred at a border post (difficult to verify)',
        },

        # Vague or generic incident description
        'vague_description': {
            'weight': 0.20,
            'description': 'Incident description is suspiciously non-specific',
        },

        # Staged incident in known high-risk area with maximum coverage claim
        'staged_incident': {
            'weight': 0.12,
            'high_risk_areas': ['Township Road', 'Industrial Area', 'Commuter Terminus'],
            'description': 'Staged incident in high-risk area with near-maximum claim',
        },

        # Parts or accessory theft inflated beyond plausible value
        'parts_theft_inflation': {
            'weight': 0.10,
            'common_parts': ['Engine', 'Gearbox', 'Wheels', 'Catalytic Converter'],
            'description': 'Theft claim value exceeds typical market cost of parts',
        },
    }