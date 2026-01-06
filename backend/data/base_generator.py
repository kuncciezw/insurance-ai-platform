"""
Base data generator utilities
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
        # VIN is 17 characters, excluding I, O, Q
        valid_chars = 'ABCDEFGHJKLMNPRSTUVWXYZ0123456789'
        return ''.join(random.choices(valid_chars, k=17))
    
    @staticmethod
    def random_date_between(start_date, end_date):
        """Generate random date between two dates"""
        time_between = end_date - start_date
        days_between = time_between.days
        random_days = random.randrange(days_between)
        return start_date + timedelta(days=random_days)
    
    @staticmethod
    def random_datetime_between(start_datetime, end_datetime):
        """Generate random datetime between two datetimes"""
        # Safety check: ensure start is before end
        if start_datetime >= end_datetime:
            # If dates are invalid, return start datetime
            return start_datetime
        
        seconds_between = int((end_datetime - start_datetime).total_seconds())
        
        # Safety check for empty range
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
    """Configuration constants for insurance data generation"""
    
    # Vehicle makes and models with market values
    VEHICLES = {
        'Toyota': {
            'models': ['Camry', 'Corolla', 'RAV4', 'Highlander', 'Prius'],
            'base_value': (20000, 45000),
            'type': 'SEDAN'
        },
        'Honda': {
            'models': ['Accord', 'Civic', 'CR-V', 'Pilot', 'Odyssey'],
            'base_value': (22000, 48000),
            'type': 'SEDAN'
        },
        'Ford': {
            'models': ['F-150', 'Explorer', 'Escape', 'Mustang', 'Edge'],
            'base_value': (25000, 55000),
            'type': 'TRUCK'
        },
        'Chevrolet': {
            'models': ['Silverado', 'Equinox', 'Malibu', 'Tahoe', 'Traverse'],
            'base_value': (24000, 52000),
            'type': 'TRUCK'
        },
        'BMW': {
            'models': ['3 Series', '5 Series', 'X3', 'X5', 'X7'],
            'base_value': (40000, 85000),
            'type': 'SEDAN'
        },
        'Mercedes-Benz': {
            'models': ['C-Class', 'E-Class', 'GLC', 'GLE', 'S-Class'],
            'base_value': (42000, 95000),
            'type': 'SEDAN'
        },
        'Tesla': {
            'models': ['Model 3', 'Model Y', 'Model S', 'Model X'],
            'base_value': (40000, 100000),
            'type': 'SEDAN'
        },
        'Nissan': {
            'models': ['Altima', 'Sentra', 'Rogue', 'Pathfinder', 'Murano'],
            'base_value': (20000, 42000),
            'type': 'SEDAN'
        },
        'Jeep': {
            'models': ['Wrangler', 'Grand Cherokee', 'Cherokee', 'Compass', 'Gladiator'],
            'base_value': (28000, 58000),
            'type': 'SUV'
        },
        'Audi': {
            'models': ['A4', 'A6', 'Q5', 'Q7', 'Q8'],
            'base_value': (38000, 80000),
            'type': 'SEDAN'
        }
    }
    
    # US States
    US_STATES = [
        'Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado',
        'Connecticut', 'Delaware', 'Florida', 'Georgia', 'Hawaii', 'Idaho',
        'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana',
        'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota',
        'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada',
        'New Hampshire', 'New Jersey', 'New Mexico', 'New York',
        'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon',
        'Pennsylvania', 'Rhode Island', 'South Carolina', 'South Dakota',
        'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington',
        'West Virginia', 'Wisconsin', 'Wyoming'
    ]
    
    # Occupations with income ranges
    OCCUPATIONS = {
        'EMPLOYED': {
            'titles': [
                'Software Engineer', 'Teacher', 'Nurse', 'Accountant',
                'Marketing Manager', 'Sales Representative', 'Engineer',
                'Project Manager', 'Business Analyst', 'HR Manager'
            ],
            'income_range': (40000, 120000)
        },
        'SELF_EMPLOYED': {
            'titles': [
                'Consultant', 'Contractor', 'Freelancer', 'Business Owner',
                'Real Estate Agent', 'Attorney', 'Doctor', 'Dentist'
            ],
            'income_range': (50000, 250000)
        },
        'RETIRED': {
            'titles': ['Retired'],
            'income_range': (25000, 80000)
        },
        'STUDENT': {
            'titles': ['Student'],
            'income_range': (0, 30000)
        },
        'UNEMPLOYED': {
            'titles': ['Unemployed'],
            'income_range': (0, 15000)
        }
    }
    
    # Incident locations (common types)
    INCIDENT_LOCATIONS = [
        'Highway', 'Parking Lot', 'Residential Street', 'Downtown',
        'Shopping Center', 'Intersection', 'Highway Exit', 'Rural Road',
        'School Zone', 'Office Complex', 'Gas Station', 'Restaurant Parking',
        'Mall Parking Structure', 'Side Street', 'Main Street'
    ]
    
    # Fraud indicators and patterns
    FRAUD_PATTERNS = {
        'amount_inflation': {
            'weight': 0.3,
            'multiplier': (1.5, 3.0)
        },
        'suspicious_timing': {
            'weight': 0.2,
            'days_after_policy': (0, 30)
        },
        'no_police_report': {
            'weight': 0.25,
            'severe_claims_only': True
        },
        'multiple_claims': {
            'weight': 0.15,
            'claims_per_year': (3, 6)
        },
        'suspicious_witnesses': {
            'weight': 0.1,
            'witness_pattern': 'always_present'
        }
    }