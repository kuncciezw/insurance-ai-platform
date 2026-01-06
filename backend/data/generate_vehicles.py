"""
Generate synthetic vehicle data
"""

import random
from datetime import datetime
from decimal import Decimal
from .base_generator import DataGenerator, InsuranceDataConfig


class VehicleGenerator(DataGenerator):
    """Generate realistic vehicle data"""
    
    VEHICLE_TYPES = {
        'SEDAN': ['SEDAN', 'COUPE', 'HATCHBACK'],
        'SUV': ['SUV'],
        'TRUCK': ['TRUCK'],
        'VAN': ['VAN'],
        'SPORTS': ['SPORTS']
    }
    
    FUEL_TYPES = ['PETROL', 'DIESEL', 'ELECTRIC', 'HYBRID']
    
    @staticmethod
    def generate_vehicle(policyholder_id, index):
        """Generate a single vehicle for a policyholder"""
        
        # Select random make and model
        make = random.choice(list(InsuranceDataConfig.VEHICLES.keys()))
        vehicle_info = InsuranceDataConfig.VEHICLES[make]
        model = random.choice(vehicle_info['models'])
        
        # Vehicle year (weighted towards recent years)
        current_year = datetime.now().year
        year = VehicleGenerator.weighted_choice(
            list(range(current_year - 15, current_year + 1)),
            [1, 1, 2, 2, 3, 4, 5, 6, 7, 8, 10, 12, 15, 18, 20, 15]
        )
        
        # Vehicle type
        base_type = vehicle_info['type']
        if base_type == 'SEDAN':
            vehicle_type = VehicleGenerator.weighted_choice(
                VehicleGenerator.VEHICLE_TYPES['SEDAN'],
                [0.7, 0.2, 0.1]
            )
        else:
            vehicle_type = base_type
        
        # Market value (depreciates with age)
        base_value_range = vehicle_info['base_value']
        base_value = random.uniform(base_value_range[0], base_value_range[1])
        vehicle_age = current_year - year
        depreciation = 0.85 ** vehicle_age  # 15% per year
        market_value = Decimal(base_value * depreciation)
        
        # Fuel type (Tesla is electric, luxury brands more likely hybrid)
        if make == 'Tesla':
            fuel_type = 'ELECTRIC'
        elif make in ['BMW', 'Mercedes-Benz', 'Audi']:
            fuel_type = VehicleGenerator.weighted_choice(
                VehicleGenerator.FUEL_TYPES,
                [0.4, 0.2, 0.2, 0.2]
            )
        else:
            fuel_type = VehicleGenerator.weighted_choice(
                VehicleGenerator.FUEL_TYPES,
                [0.6, 0.2, 0.1, 0.1]
            )
        
        # Engine capacity based on fuel type and vehicle type
        if fuel_type == 'ELECTRIC':
            engine_capacity = 0
        elif vehicle_type in ['TRUCK', 'SUV']:
            engine_capacity = random.randint(2500, 5500)
        else:
            engine_capacity = random.randint(1400, 3500)
        
        # Seating capacity
        if vehicle_type == 'TRUCK':
            seating_capacity = random.choice([2, 5])
        elif vehicle_type == 'VAN':
            seating_capacity = random.choice([7, 8])
        elif vehicle_type == 'SUV':
            seating_capacity = random.choice([5, 7])
        else:
            seating_capacity = random.choice([4, 5])
        
        # Odometer reading (higher for older vehicles)
        avg_miles_per_year = random.randint(10000, 15000)
        odometer_reading = vehicle_age * avg_miles_per_year + random.randint(-2000, 2000)
        odometer_reading = max(0, odometer_reading)
        
        # Safety features (newer vehicles more likely to have them)
        has_anti_theft = random.random() > (0.3 if year > current_year - 5 else 0.6)
        has_airbags = year > 2000 or random.random() > 0.1
        has_abs = year > 2005 or random.random() > 0.2
        
        # Modifications (more likely on older, cheaper vehicles)
        is_modified = random.random() < (0.15 if market_value < 30000 and vehicle_age > 5 else 0.05)
        
        vehicle = {
            'vehicle_id': VehicleGenerator.generate_id('VEH', 10),
            'policyholder_id': policyholder_id,
            'make': make,
            'model': model,
            'year': year,
            'vehicle_type': vehicle_type,
            'vin': VehicleGenerator.generate_vin(),
            'registration_number': f"{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}{random.randint(1000, 9999)}",
            'engine_capacity': engine_capacity,
            'fuel_type': fuel_type,
            'seating_capacity': seating_capacity,
            'market_value': market_value,
            'odometer_reading': odometer_reading,
            'has_anti_theft': has_anti_theft,
            'has_airbags': has_airbags,
            'has_abs': has_abs,
            'is_modified': is_modified,
        }
        
        return vehicle
    
    @staticmethod
    def generate_batch(policyholders):
        """Generate vehicles for policyholders"""
        print(f"Generating vehicles for {len(policyholders)} policyholders...")
        vehicles = []
        
        for i, policyholder in enumerate(policyholders):
            # Most policyholders have 1 vehicle, some have 2-3
            num_vehicles = VehicleGenerator.weighted_choice([1, 2, 3], [0.7, 0.25, 0.05])
            
            for v in range(num_vehicles):
                vehicle = VehicleGenerator.generate_vehicle(
                    policyholder['policy_holder_id'],
                    len(vehicles)
                )
                vehicles.append(vehicle)
            
            if (i + 1) % 100 == 0:
                print(f"  Generated vehicles for {i + 1}/{len(policyholders)} policyholders")
        
        print(f"✓ Generated {len(vehicles)} vehicles")
        return vehicles