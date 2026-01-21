"""
Main script to generate all synthetic insurance data
"""

import os
import sys
import django
import csv
from decimal import Decimal
from datetime import datetime

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.fraud_detection.models import Policyholder, Vehicle, Policy, Claim
from .generate_policyholders import PolicyholderGenerator
from .generate_vehicles import VehicleGenerator
from .generate_policies import PolicyGenerator
from .generate_claims import ClaimGenerator


def save_to_csv(data, filename, fieldnames):
    """Save data to CSV file"""
    filepath = os.path.join('data', 'generated', filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    print(f"✓ Saved {len(data)} records to {filepath}")


def load_to_database(policyholders, vehicles, policies, claims):
    """Load generated data into Django database"""
    print("\n" + "="*60)
    print("LOADING DATA INTO DATABASE")
    print("="*60)
    
    # Clear existing data
    print("\nClearing existing data...")
    Claim.objects.all().delete()
    Policy.objects.all().delete()
    Vehicle.objects.all().delete()
    Policyholder.objects.all().delete()
    print("✓ Existing data cleared")
    
    # Load policyholders
    print(f"\nLoading {len(policyholders)} policyholders...")
    policyholder_objects = []
    for ph in policyholders:
        obj = Policyholder(
            policy_holder_id=ph['policy_holder_id'],
            first_name=ph['first_name'],
            last_name=ph['last_name'],
            date_of_birth=ph['date_of_birth'],
            gender=ph['gender'],
            email=ph['email'],
            phone_number=ph['phone_number'],
            address_line1=ph['address_line1'],
            address_line2=ph['address_line2'],
            city=ph['city'],
            state=ph['state'],
            postal_code=ph['postal_code'],
            country=ph['country'],
            marital_status=ph['marital_status'],
            occupation=ph['occupation'],
            annual_income=ph['annual_income'],
            credit_score=ph['credit_score'],
            years_with_company=ph['years_with_company'],
            is_active=ph['is_active']
        )
        policyholder_objects.append(obj)
    
    Policyholder.objects.bulk_create(policyholder_objects, batch_size=500)
    print(f"✓ Loaded {len(policyholder_objects)} policyholders")
    
    # Create lookup dictionary for database objects
    ph_db_dict = {ph.policy_holder_id: ph for ph in Policyholder.objects.all()}
    
    # Load vehicles
    print(f"\nLoading {len(vehicles)} vehicles...")
    vehicle_objects = []
    for v in vehicles:
        obj = Vehicle(
            vehicle_id=v['vehicle_id'],
            make=v['make'],
            model=v['model'],
            year=v['year'],
            vehicle_type=v['vehicle_type'],
            vin=v['vin'],
            registration_number=v['registration_number'],
            engine_capacity=v['engine_capacity'],
            fuel_type=v['fuel_type'],
            seating_capacity=v['seating_capacity'],
            market_value=v['market_value'],
            odometer_reading=v['odometer_reading'],
            has_anti_theft=v['has_anti_theft'],
            has_airbags=v['has_airbags'],
            has_abs=v['has_abs'],
            is_modified=v['is_modified'],
            policyholder=ph_db_dict[v['policyholder_id']]
        )
        vehicle_objects.append(obj)
    
    Vehicle.objects.bulk_create(vehicle_objects, batch_size=500)
    print(f"✓ Loaded {len(vehicle_objects)} vehicles")
    
    # Create lookup dictionary for vehicles
    v_db_dict = {v.vehicle_id: v for v in Vehicle.objects.all()}
    
    # Load policies
    print(f"\nLoading {len(policies)} policies...")
    policy_objects = []
    for p in policies:
        obj = Policy(
            policy_number=p['policy_number'],
            policyholder=ph_db_dict[p['policyholder_id']],
            vehicle=v_db_dict[p['vehicle_id']],
            policy_type=p['policy_type'],
            coverage_level=p['coverage_level'],
            status=p['status'],
            premium_amount=p['premium_amount'],
            coverage_amount=p['coverage_amount'],
            deductible=p['deductible'],
            start_date=p['start_date'],
            end_date=p['end_date'],
            has_roadside_assistance=p['has_roadside_assistance'],
            has_rental_coverage=p['has_rental_coverage'],
            has_glass_coverage=p['has_glass_coverage']
        )
        policy_objects.append(obj)
    
    Policy.objects.bulk_create(policy_objects, batch_size=500)
    print(f"✓ Loaded {len(policy_objects)} policies")
    
    # Create lookup dictionary for policies
    pol_db_dict = {p.policy_number: p for p in Policy.objects.all()}
    
    # Load claims
    print(f"\nLoading {len(claims)} claims...")
    claim_objects = []
    for c in claims:
        obj = Claim(
            claim_number=c['claim_number'],
            policy=pol_db_dict[c['policy_number']],
            policyholder=ph_db_dict[c['policyholder_id']],
            vehicle=v_db_dict[c['vehicle_id']],
            claim_type=c['claim_type'],
            claim_status=c['claim_status'],
            severity=c['severity'],
            incident_date=c['incident_date'],
            incident_location=c['incident_location'],
            incident_description=c['incident_description'],
            police_report_filed=c['police_report_filed'],
            police_report_number=c['police_report_number'],
            witnesses_present=c['witnesses_present'],
            number_of_witnesses=c['number_of_witnesses'],
            number_of_vehicles_involved=c['number_of_vehicles_involved'],
            number_of_injuries=c['number_of_injuries'],
            third_party_involved=c['third_party_involved'],
            claimed_amount=c['claimed_amount'],
            approved_amount=c['approved_amount'],
            paid_amount=c['paid_amount'],
            fraud_score=c['fraud_score'],
            is_fraudulent=c['is_fraudulent'],
            fraud_reason=c['fraud_reason'],
            submitted_date=c['submitted_date'],
            reviewed_date=c['reviewed_date'],
            closed_date=c['closed_date']
        )
        claim_objects.append(obj)
    
    Claim.objects.bulk_create(claim_objects, batch_size=500)
    print(f"✓ Loaded {len(claim_objects)} claims")
    
    print("\n✓ All data successfully loaded into database!")


def generate_all_data(num_policyholders=1000, fraud_rate=0.15, save_csv=True, load_db=True):
    """
    Generate complete insurance dataset
    
    Args:
        num_policyholders: Number of policyholders to generate
        fraud_rate: Percentage of fraudulent claims (0.0 to 1.0)
        save_csv: Whether to save data to CSV files
        load_db: Whether to load data into database
    """
    print("="*60)
    print("INSURANCE AI PLATFORM - DATA GENERATION")
    print("="*60)
    print(f"\nConfiguration:")
    print(f"  - Policyholders: {num_policyholders}")
    print(f"  - Fraud Rate: {fraud_rate*100}%")
    print(f"  - Save to CSV: {save_csv}")
    print(f"  - Load to Database: {load_db}")
    print("\n" + "="*60)
    
    # Generate policyholders
    print("\n[1/4] GENERATING POLICYHOLDERS")
    print("-"*60)
    policyholders = PolicyholderGenerator.generate_batch(num_policyholders)
    
    # Generate vehicles
    print("\n[2/4] GENERATING VEHICLES")
    print("-"*60)
    vehicles = VehicleGenerator.generate_batch(policyholders)
    
    # Generate policies
    print("\n[3/4] GENERATING POLICIES")
    print("-"*60)
    policies = PolicyGenerator.generate_batch(policyholders, vehicles)
    
    # Generate claims
    print("\n[4/4] GENERATING CLAIMS")
    print("-"*60)
    claims = ClaimGenerator.generate_batch(policyholders, vehicles, policies, fraud_rate)
    
    # Save to CSV
    if save_csv:
        print("\n" + "="*60)
        print("SAVING DATA TO CSV FILES")
        print("="*60 + "\n")
        
        save_to_csv(
            policyholders,
            'policyholders.csv',
            ['policy_holder_id','national_id', 'first_name', 'last_name', 'date_of_birth', 'gender',
             'email', 'phone_number', 'address_line1', 'address_line2', 'city', 'state',
             'postal_code', 'country', 'marital_status', 'occupation', 'monthly_income','annual_income',
             'credit_score','credit_rating', 'years_with_company', 'is_active']
        )
        
        save_to_csv(
            vehicles,
            'vehicles.csv',
            ['vehicle_id', 'policyholder_id', 'make', 'model', 'year', 'vehicle_type',
             'vin', 'registration_number', 'engine_capacity', 'fuel_type', 'seating_capacity',
             'market_value', 'odometer_reading', 'has_anti_theft', 'has_airbags', 'has_abs',
             'is_modified']
        )
        
        save_to_csv(
            policies,
            'policies.csv',
            ['policy_number', 'policyholder_id', 'vehicle_id', 'policy_type', 'coverage_level',
             'status', 'premium_amount', 'coverage_amount', 'deductible', 'start_date', 'end_date',
             'has_roadside_assistance', 'has_rental_coverage', 'has_glass_coverage']
        )
        
        save_to_csv(
            claims,
            'claims.csv',
            ['claim_number', 'policy_number', 'policyholder_id', 'vehicle_id', 'claim_type',
             'claim_status', 'severity', 'incident_date', 'incident_location', 'incident_description',
             'police_report_filed', 'police_report_number', 'witnesses_present', 'number_of_witnesses',
             'number_of_vehicles_involved', 'number_of_injuries', 'third_party_involved',
             'claimed_amount', 'approved_amount', 'paid_amount', 'fraud_score', 'is_fraudulent',
             'fraud_reason', 'submitted_date', 'reviewed_date', 'closed_date']
        )
    
    # Load to database
    if load_db:
        load_to_database(policyholders, vehicles, policies, claims)
    
    # Print summary
    print("\n" + "="*60)
    print("DATA GENERATION COMPLETE")
    print("="*60)
    print(f"\nGenerated Dataset Summary:")
    print(f"  - Policyholders: {len(policyholders)}")
    print(f"  - Vehicles: {len(vehicles)}")
    print(f"  - Policies: {len(policies)}")
    print(f"  - Claims: {len(claims)}")
    print(f"    • Legitimate: {len([c for c in claims if not c['is_fraudulent']])}")
    print(f"    • Fraudulent: {len([c for c in claims if c['is_fraudulent']])}")
    print("\n" + "="*60)
    
    return policyholders, vehicles, policies, claims


if __name__ == '__main__':
    # Generate data with default parameters
    # Adjust parameters as needed:
    # - num_policyholders: 500, 1000, 2000, 5000
    # - fraud_rate: 0.10 (10%), 0.15 (15%), 0.20 (20%)
    
    generate_all_data(
        num_policyholders=1000,
        fraud_rate=0.15,
        save_csv=True,
        load_db=True
    )