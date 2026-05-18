"""
Main script to generate all synthetic insurance data
REFACTORED VERSION — aligns with updated database schema:
  Policyholder : removed postal_code; added has_driving_license,
                 has_defensive_license, is_medical_license_valid
  Vehicle      : removed vehicle_id; manufacture_year replaces year
  Policy       : vehicle referenced by VIN (vehicle_vin); added currency
  Claim        : removed police_report_filed, police_report_number,
                 witnesses_present, number_of_witnesses,
                 number_of_injuries, third_party_involved;
                 added payment_method, incident_evidence

CRITICAL: bulk_create() bypasses Django's save(), so all computed
fields (annual_income, credit_score, premium_amount, claimed_amount, …)
are explicitly set here rather than relying on model-level calculations.
"""

import os
import sys
import django
import csv
from decimal import Decimal
from datetime import datetime

# ---------------------------------------------------------------------------
# Django setup
# ---------------------------------------------------------------------------
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.fraud_detection.models import Policyholder, Vehicle, Policy, Claim
from .generate_policyholders import PolicyholderGenerator
from .generate_vehicles       import VehicleGenerator
from .generate_policies       import PolicyGenerator
from .generate_claims         import ClaimGenerator


# ---------------------------------------------------------------------------
# CSV helpers
# ---------------------------------------------------------------------------

def save_to_csv(data: list, filename: str, fieldnames: list) -> None:
    """Persist a list of dicts to a CSV file."""
    filepath = os.path.join('data', 'generated', filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with open(filepath, 'w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(data)

    print(f"✓ Saved {len(data):,} records to {filepath}")


# ---------------------------------------------------------------------------
# Database loader
# ---------------------------------------------------------------------------

def load_to_database(policyholders: list, vehicles: list,
                      policies: list, claims: list) -> None:
    """Bulk-load all generated data into the Django database."""

    print("\n" + "=" * 60)
    print("LOADING DATA INTO DATABASE")
    print("=" * 60)

    # Clear existing data (order matters for FK constraints)
    print("\nClearing existing data...")
    Claim.objects.all().delete()
    Policy.objects.all().delete()
    Vehicle.objects.all().delete()
    Policyholder.objects.all().delete()
    print("✓ Existing data cleared")

    # ------------------------------------------------------------------
    # Policyholders
    # postal_code removed; has_driving_license / has_defensive_license /
    # is_medical_license_valid added; annual_income explicitly set.
    # ------------------------------------------------------------------
    print(f"\nLoading {len(policyholders):,} policyholders...")
    ph_objects = [
        Policyholder(
            policy_holder_id        = ph['policy_holder_id'],
            national_id             = ph['national_id'],
            first_name              = ph['first_name'],
            last_name               = ph['last_name'],
            date_of_birth           = ph['date_of_birth'],
            gender                  = ph['gender'],
            email                   = ph['email'],
            phone_number            = ph['phone_number'],
            address_line1           = ph['address_line1'],
            address_line2           = ph['address_line2'],
            city                    = ph['city'],
            state                   = ph['state'],
            # postal_code removed from schema
            country                 = ph['country'],
            marital_status          = ph['marital_status'],
            occupation              = ph['occupation'],
            monthly_income          = ph['monthly_income'],
            credit_score            = ph['credit_score'],           # algorithm output
            years_with_company      = ph['years_with_company'],
            has_driving_license     = ph['has_driving_license'],    # new
            has_defensive_license   = ph['has_defensive_license'],  # new
            is_medical_license_valid = ph['is_medical_license_valid'],  # new
            is_active               = ph['is_active'],
        )
        for ph in policyholders
    ]
    Policyholder.objects.bulk_create(ph_objects, batch_size=500)
    print(f"✓ Loaded {len(ph_objects):,} policyholders")

    # Build lookup keyed by policy_holder_id (custom field)
    ph_db_dict = {ph.policy_holder_id: ph for ph in Policyholder.objects.all()}

    # ------------------------------------------------------------------
    # Vehicles
    # vehicle_id removed (Django auto pk); manufacture_year replaces year.
    # ------------------------------------------------------------------
    print(f"\nLoading {len(vehicles):,} vehicles...")
    v_objects = [
        Vehicle(
            # no vehicle_id — Django auto pk
            make                = v['make'],
            model               = v['model'],
            manufacture_year    = v['manufacture_year'],   # renamed from year
            vehicle_type        = v['vehicle_type'],
            vin                 = v['vin'],
            registration_number = v['registration_number'],
            engine_capacity     = v['engine_capacity'],
            fuel_type           = v['fuel_type'],
            seating_capacity    = v['seating_capacity'],
            market_value        = v['market_value'],
            odometer_reading    = v['odometer_reading'],
            has_anti_theft      = v['has_anti_theft'],
            has_airbags         = v['has_airbags'],
            has_abs             = v['has_abs'],
            is_modified         = v['is_modified'],
            policyholder        = ph_db_dict[v['policyholder_id']],
        )
        for v in vehicles
    ]
    Vehicle.objects.bulk_create(v_objects, batch_size=500)
    print(f"✓ Loaded {len(v_objects):,} vehicles")

    # Build lookup keyed by VIN (natural unique key — replaces vehicle_id)
    v_db_dict = {v.vin: v for v in Vehicle.objects.all()}

    # ------------------------------------------------------------------
    # Policies
    # vehicle referenced by VIN; currency added; premium_amount explicit.
    # ------------------------------------------------------------------
    print(f"\nLoading {len(policies):,} policies...")
    pol_objects = [
        Policy(
            policy_number           = p['policy_number'],
            policyholder            = ph_db_dict[p['policyholder_id']],
            vehicle                 = v_db_dict[p['vehicle_vin']],  # VIN lookup
            policy_type             = p['policy_type'],
            coverage_level          = p['coverage_level'],
            currency                = p['currency'],                # new
            status                  = p['status'],
            premium_amount          = p['premium_amount'],          # explicit
            coverage_amount         = p['coverage_amount'],
            deductible              = p['deductible'],
            start_date              = p['start_date'],
            end_date                = p['end_date'],
            has_roadside_assistance = p['has_roadside_assistance'],
            has_rental_coverage     = p['has_rental_coverage'],
            has_glass_coverage      = p['has_glass_coverage'],
        )
        for p in policies
    ]
    Policy.objects.bulk_create(pol_objects, batch_size=500)
    print(f"✓ Loaded {len(pol_objects):,} policies")

    # Build lookup keyed by policy_number
    pol_db_dict = {p.policy_number: p for p in Policy.objects.all()}

    # ------------------------------------------------------------------
    # Claims
    # Removed fields: police_report_filed, police_report_number,
    #                 witnesses_present, number_of_witnesses,
    #                 number_of_injuries, third_party_involved
    # Added fields  : payment_method, incident_evidence
    # claimed_amount, approved_amount, paid_amount all explicit.
    # ------------------------------------------------------------------
    print(f"\nLoading {len(claims):,} claims...")
    cl_objects = [
        Claim(
            claim_number                = c['claim_number'],
            policy                      = pol_db_dict[c['policy_number']],
            policyholder                = ph_db_dict[c['policyholder_id']],
            vehicle                     = v_db_dict[c['vehicle_vin']],  # VIN lookup
            claim_type                  = c['claim_type'],
            claim_status                = c['claim_status'],
            severity                    = c['severity'],
            incident_date               = c['incident_date'],
            incident_location           = c['incident_location'],
            number_of_vehicles_involved = c['number_of_vehicles_involved'],
            claimed_amount              = c['claimed_amount'],          # explicit
            approved_amount             = c['approved_amount'],
            paid_amount                 = c['paid_amount'],
            payment_method              = c['payment_method'],          # new
            incident_evidence           = c['incident_evidence'],       # new
            fraud_score                 = c['fraud_score'],
            is_fraudulent               = c['is_fraudulent'],
            fraud_reason                = c['fraud_reason'],
            submitted_date              = c['submitted_date'],
            reviewed_date               = c['reviewed_date'],
            closed_date                 = c['closed_date'],
        )
        for c in claims
    ]
    Claim.objects.bulk_create(cl_objects, batch_size=500)
    print(f"✓ Loaded {len(cl_objects):,} claims")

    print("\n✅ All data successfully loaded into database!")


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def generate_all_data(num_policyholders: int = 1000,
                       fraud_rate: float = 0.15,
                       save_csv: bool = True,
                       load_db: bool = True):
    """
    Generate a complete synthetic insurance dataset.

    Args:
        num_policyholders : Number of policyholders to generate
        fraud_rate        : Fraction of fraudulent claims (0.0 – 1.0)
        save_csv          : Persist data to CSV files
        load_db           : Load data into the Django database
    """
    print("=" * 60)
    print("INSURANCE AI PLATFORM — DATA GENERATION")
    print("=" * 60)
    print(f"\nConfiguration:")
    print(f"  Policyholders : {num_policyholders:,}")
    print(f"  Fraud rate    : {fraud_rate * 100:.1f}%")
    print(f"  Save CSV      : {save_csv}")
    print(f"  Load DB       : {load_db}")
    print("\n" + "=" * 60)

    # [1] Policyholders
    print("\n[1/4] GENERATING POLICYHOLDERS")
    print("-" * 60)
    policyholders = PolicyholderGenerator.generate_batch(num_policyholders)

    # [2] Vehicles
    print("\n[2/4] GENERATING VEHICLES")
    print("-" * 60)
    vehicles = VehicleGenerator.generate_batch(policyholders)

    # [3] Policies
    print("\n[3/4] GENERATING POLICIES")
    print("-" * 60)
    policies = PolicyGenerator.generate_batch(policyholders, vehicles)

    # [4] Claims
    print("\n[4/4] GENERATING CLAIMS")
    print("-" * 60)
    claims = ClaimGenerator.generate_batch(
        policyholders, vehicles, policies, fraud_rate
    )

    # ------------------------------------------------------------------
    # CSV export — headers strictly match the new dict keys
    # ------------------------------------------------------------------
    if save_csv:
        print("\n" + "=" * 60)
        print("SAVING DATA TO CSV FILES")
        print("=" * 60 + "\n")

        save_to_csv(
            policyholders,
            'policyholders.csv',
            [
                'policy_holder_id', 'national_id', 'first_name', 'last_name',
                'date_of_birth', 'gender', 'email', 'phone_number',
                'address_line1', 'address_line2', 'city', 'state',
                # 'postal_code' removed
                'country', 'marital_status', 'occupation',
                'monthly_income', 'annual_income',
                'credit_rating', 'credit_score',
                'years_with_company',
                'has_driving_license',       # new
                'has_defensive_license',     # new
                'is_medical_license_valid',  # new
                'is_active',
            ]
        )

        save_to_csv(
            vehicles,
            'vehicles.csv',
            [
                # 'vehicle_id' removed
                'policyholder_id', 'make', 'model',
                'manufacture_year',          # renamed from 'year'
                'vehicle_type', 'vin', 'registration_number',
                'engine_capacity', 'fuel_type', 'seating_capacity',
                'market_value', 'odometer_reading',
                'has_anti_theft', 'has_airbags', 'has_abs', 'is_modified',
            ]
        )

        save_to_csv(
            policies,
            'policies.csv',
            [
                'policy_number', 'policyholder_id',
                'vehicle_vin',               # replaces 'vehicle_id'
                'policy_type', 'coverage_level',
                'currency',                  # new
                'status', 'premium_amount', 'coverage_amount', 'deductible',
                'start_date', 'end_date',
                'has_roadside_assistance', 'has_rental_coverage', 'has_glass_coverage',
            ]
        )

        save_to_csv(
            claims,
            'claims.csv',
            [
                'claim_number', 'policy_number', 'policyholder_id',
                'vehicle_vin',               # replaces 'vehicle_id'
                'claim_type', 'claim_status', 'severity',
                'incident_date', 'incident_location', 'incident_description',
                # Removed: police_report_filed, police_report_number,
                #          witnesses_present, number_of_witnesses,
                #          number_of_injuries, third_party_involved
                'number_of_vehicles_involved',
                'claimed_amount', 'approved_amount', 'paid_amount',
                'payment_method',            # new
                'incident_evidence',         # new
                'fraud_score', 'is_fraudulent', 'fraud_reason',
                'submitted_date', 'reviewed_date', 'closed_date',
            ]
        )

    # ------------------------------------------------------------------
    # Database load
    # ------------------------------------------------------------------
    if load_db:
        load_to_database(policyholders, vehicles, policies, claims)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    fraudulent = [c for c in claims if c['is_fraudulent']]
    print("\n" + "=" * 60)
    print("DATA GENERATION COMPLETE")
    print("=" * 60)
    print(f"\nGenerated Dataset Summary:")
    print(f"  Policyholders : {len(policyholders):,}")
    print(f"  Vehicles      : {len(vehicles):,}")
    print(f"  Policies      : {len(policies):,}")
    print(f"  Claims        : {len(claims):,}")
    print(f"    • Legitimate  : {len(claims) - len(fraudulent):,}")
    print(f"    • Fraudulent  : {len(fraudulent):,}")
    print("\n" + "=" * 60)

    return policyholders, vehicles, policies, claims


if __name__ == '__main__':
    generate_all_data(
        num_policyholders=1000,
        fraud_rate=0.15,
        save_csv=True,
        load_db=True,
    )