"""
Quick script to generate synthetic data
Run from backend directory: python generate_data.py
"""

import os
import sys

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run data generation
from data.generate_all_data import generate_all_data

if __name__ == '__main__':
    print("\n🚀 Starting Insurance Data Generation...\n")
    
    # You can modify these parameters:
    NUM_POLICYHOLDERS = 1000  # Number of policyholders to generate
    FRAUD_RATE = 0.15          # 15% of claims will be fraudulent
    
    generate_all_data(
        num_policyholders=NUM_POLICYHOLDERS,
        fraud_rate=FRAUD_RATE,
        save_csv=True,
        load_db=True
    )
    
    print("\n✅ Data generation completed successfully!")
    print("\nYou can now:")
    print("  1. View the data in Django Admin: http://localhost:8000/admin")
    print("  2. Access CSV files in: backend/data/generated/")
    print("  3. Use the API endpoints to query the data")
    print("\n")