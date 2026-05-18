"""
Generate synthetic vehicle data - Zimbabwe Market
REFACTORED VERSION
- Removed vehicle_id generation (model now uses Django auto pk)
- Renamed 'year' → 'manufacture_year' throughout
- All internal vehicle_age calculations use manufacture_year
- Zimbabwe import-market depreciation model preserved
"""

import random
from datetime import datetime
from decimal import Decimal
from .base_generator import DataGenerator, InsuranceDataConfig


class VehicleGenerator(DataGenerator):
    """Generate realistic Zimbabwe vehicle data"""

    VEHICLE_TYPES = {
        'SEDAN':  ['SEDAN', 'HATCHBACK'],
        'SUV':    ['SUV'],
        'TRUCK':  ['TRUCK', 'PICKUP'],
        'VAN':    ['VAN', 'MINIBUS'],
        'KOMBI':  ['KOMBI'],   # Common for public transport in Zimbabwe
    }

    FUEL_TYPES = ['PETROL', 'DIESEL', 'HYBRID']   # Electric rare in Zimbabwe

    @staticmethod
    def generate_vehicle(policyholder_id, index):
        """Generate a single vehicle for a Zimbabwe policyholder"""

        # Make / model selection (Zimbabwe market)
        make         = random.choice(list(InsuranceDataConfig.VEHICLES.keys()))
        vehicle_info = InsuranceDataConfig.VEHICLES[make]
        model        = random.choice(vehicle_info['models'])

        # Manufacture year — Zimbabwe has many older import vehicles
        current_year   = datetime.now().year
        manufacture_year = VehicleGenerator.weighted_choice(
            list(range(current_year - 25, current_year + 1)),
            # More weight on 2005-2015 band
            [1, 1, 1, 2, 2, 3, 3, 4, 5, 6, 7, 8, 10, 12, 10, 8, 7, 6, 5, 4, 3, 3, 2, 2, 1, 1]
        )

        # Vehicle type
        base_type = vehicle_info['type']

        if make in ('Toyota', 'Nissan', 'Isuzu', 'Ford') and model in (
            'Hilux', 'Navara', 'D-Max', 'Ranger'
        ):
            vehicle_type = 'TRUCK'
        elif make in ('Toyota', 'Nissan') and model in ('Land Cruiser', 'Patrol', 'Fortuner'):
            vehicle_type = 'SUV'
        elif base_type == 'SEDAN':
            vehicle_type = VehicleGenerator.weighted_choice(
                VehicleGenerator.VEHICLE_TYPES['SEDAN'], [0.7, 0.3]
            )
        else:
            vehicle_type = base_type

        # ----------------------------------------------------------------
        # Market value — Zimbabwe import-market depreciation
        # Older vehicles retain more residual value than Western markets
        # because parts and alternatives are scarce.
        # ----------------------------------------------------------------
        base_value_range = vehicle_info['base_value']
        base_value       = random.uniform(*base_value_range)
        vehicle_age      = current_year - manufacture_year   # uses manufacture_year

        if vehicle_age <= 5:
            # Steeper early depreciation: ~12% per year
            depreciation = 0.88 ** vehicle_age
        elif vehicle_age <= 15:
            # Slows down: ~8% per year after year 5
            depreciation = (0.88 ** 5) * (0.92 ** (vehicle_age - 5))
        else:
            # Zimbabwe floor — very old vehicles still have scrap/parts value
            depreciation = (0.88 ** 5) * (0.92 ** 10) * (0.97 ** (vehicle_age - 15))

        market_value = Decimal(str(round(base_value * depreciation, 2)))

        # Fuel type
        if vehicle_type in ('TRUCK', 'SUV'):
            fuel_type = VehicleGenerator.weighted_choice(
                ['DIESEL', 'PETROL'], [0.70, 0.30]
            )
        else:
            fuel_type = VehicleGenerator.weighted_choice(
                VehicleGenerator.FUEL_TYPES, [0.75, 0.20, 0.05]
            )

        # Engine capacity (cc)
        if fuel_type == 'HYBRID':
            engine_capacity = random.randint(1300, 2000)
        elif vehicle_type in ('TRUCK', 'SUV'):
            engine_capacity = random.randint(2400, 5000)
        else:
            engine_capacity = random.randint(1200, 2500)

        # Seating
        if vehicle_type == 'TRUCK':
            seating_capacity = random.choice([2, 5])
        elif vehicle_type == 'VAN':
            seating_capacity = random.choice([7, 8, 14])
        elif vehicle_type == 'KOMBI':
            seating_capacity = 14
        elif vehicle_type == 'SUV':
            seating_capacity = random.choice([5, 7])
        else:
            seating_capacity = 5

        # Odometer (km) — derived from vehicle_age using manufacture_year
        avg_km_per_year  = random.randint(15_000, 25_000)
        odometer_reading = vehicle_age * avg_km_per_year + random.randint(-3_000, 3_000)
        odometer_reading = max(0, odometer_reading)

        # Safety features — older vehicles less likely to have them
        has_anti_theft = random.random() > (0.25 if manufacture_year > current_year - 10 else 0.70)
        has_airbags    = manufacture_year > 2005 or random.random() > 0.15
        has_abs        = manufacture_year > 2008 or random.random() > 0.30

        # Modifications (common for off-road vehicles in Zimbabwe)
        is_modified = random.random() < (0.25 if vehicle_type in ('TRUCK', 'SUV') else 0.08)

        registration_number = VehicleGenerator.generate_zim_number_plate()

        vehicle = {
            # vehicle_id intentionally omitted — Django auto pk used instead
            'policyholder_id':    policyholder_id,
            'make':               make,
            'model':              model,
            'manufacture_year':   manufacture_year,   # renamed from 'year'
            'vehicle_type':       vehicle_type,
            'vin':                VehicleGenerator.generate_vin(),
            'registration_number': registration_number,
            'engine_capacity':    engine_capacity,
            'fuel_type':          fuel_type,
            'seating_capacity':   seating_capacity,
            'market_value':       market_value,
            'odometer_reading':   odometer_reading,
            'has_anti_theft':     has_anti_theft,
            'has_airbags':        has_airbags,
            'has_abs':            has_abs,
            'is_modified':        is_modified,
        }

        return vehicle

    @staticmethod
    def generate_batch(policyholders):
        """Generate vehicles for Zimbabwe policyholders"""
        print(f"Generating vehicles for {len(policyholders)} policyholders...")
        vehicles = []

        for i, policyholder in enumerate(policyholders):
            # Most policyholders own one vehicle; fewer own two or three
            num_vehicles = VehicleGenerator.weighted_choice([1, 2, 3], [0.80, 0.18, 0.02])

            for _ in range(num_vehicles):
                vehicle = VehicleGenerator.generate_vehicle(
                    policyholder['policy_holder_id'],
                    len(vehicles),
                )
                vehicles.append(vehicle)

            if (i + 1) % 100 == 0:
                print(f"  Generated vehicles for {i + 1}/{len(policyholders)} policyholders")

        print(f"✓ Generated {len(vehicles)} vehicles")
        return vehicles