"""
View statistics of generated data
"""

import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.fraud_detection.models import Policyholder, Vehicle, Policy, Claim
from django.db.models import Count, Sum, Avg


def print_statistics():
    """Print comprehensive statistics of generated data"""
    
    print("="*70)
    print("INSURANCE AI PLATFORM - DATA STATISTICS")
    print("="*70)
    
    # Policyholder statistics
    print("\n📊 POLICYHOLDER STATISTICS")
    print("-"*70)
    total_policyholders = Policyholder.objects.count()
    active_policyholders = Policyholder.objects.filter(is_active=True).count()
    
    print(f"Total Policyholders: {total_policyholders}")
    print(f"Active: {active_policyholders} ({active_policyholders/total_policyholders*100:.1f}%)")
    
    # By gender
    gender_stats = Policyholder.objects.values('gender').annotate(count=Count('id'))
    print("\nBy Gender:")
    for stat in gender_stats:
        print(f"  {stat['gender']}: {stat['count']}")
    
    # By occupation
    occupation_stats = Policyholder.objects.values('occupation').annotate(count=Count('id'))
    print("\nBy Occupation:")
    for stat in occupation_stats:
        print(f"  {stat['occupation']}: {stat['count']}")
    
    # Credit score distribution
    avg_credit_score = Policyholder.objects.aggregate(avg=Avg('credit_score'))['avg']
    print(f"\nAverage Credit Score: {avg_credit_score:.0f}")
    
    # Vehicle statistics
    print("\n🚗 VEHICLE STATISTICS")
    print("-"*70)
    total_vehicles = Vehicle.objects.count()
    print(f"Total Vehicles: {total_vehicles}")
    
    # By type
    vehicle_type_stats = Vehicle.objects.values('vehicle_type').annotate(count=Count('id'))
    print("\nBy Type:")
    for stat in vehicle_type_stats:
        print(f"  {stat['vehicle_type']}: {stat['count']}")
    
    # By fuel type
    fuel_stats = Vehicle.objects.values('fuel_type').annotate(count=Count('id'))
    print("\nBy Fuel Type:")
    for stat in fuel_stats:
        print(f"  {stat['fuel_type']}: {stat['count']}")
    
    # Top makes
    make_stats = Vehicle.objects.values('make').annotate(count=Count('id')).order_by('-count')[:5]
    print("\nTop 5 Makes:")
    for stat in make_stats:
        print(f"  {stat['make']}: {stat['count']}")
    
    # Policy statistics
    print("\n📋 POLICY STATISTICS")
    print("-"*70)
    total_policies = Policy.objects.count()
    print(f"Total Policies: {total_policies}")
    
    # By status
    status_stats = Policy.objects.values('status').annotate(count=Count('id'))
    print("\nBy Status:")
    for stat in status_stats:
        print(f"  {stat['status']}: {stat['count']}")
    
    # By type
    policy_type_stats = Policy.objects.values('policy_type').annotate(count=Count('id'))
    print("\nBy Type:")
    for stat in policy_type_stats:
        print(f"  {stat['policy_type']}: {stat['count']}")
    
    # Financial metrics
    total_premium = Policy.objects.filter(status='ACTIVE').aggregate(total=Sum('premium_amount'))['total'] or 0
    avg_premium = Policy.objects.filter(status='ACTIVE').aggregate(avg=Avg('premium_amount'))['avg'] or 0
    print(f"\nTotal Annual Premium Value: ${total_premium:,.2f}")
    print(f"Average Premium: ${avg_premium:,.2f}")
    
    # Claims statistics
    print("\n⚠️  CLAIMS STATISTICS")
    print("-"*70)
    total_claims = Claim.objects.count()
    fraudulent_claims = Claim.objects.filter(is_fraudulent=True).count()
    
    print(f"Total Claims: {total_claims}")
    print(f"Fraudulent Claims: {fraudulent_claims} ({fraudulent_claims/total_claims*100:.1f}%)")
    print(f"Legitimate Claims: {total_claims - fraudulent_claims} ({(total_claims-fraudulent_claims)/total_claims*100:.1f}%)")
    
    # By status
    claim_status_stats = Claim.objects.values('claim_status').annotate(count=Count('id'))
    print("\nBy Status:")
    for stat in claim_status_stats:
        print(f"  {stat['claim_status']}: {stat['count']}")
    
    # By type
    claim_type_stats = Claim.objects.values('claim_type').annotate(count=Count('id'))
    print("\nBy Type:")
    for stat in claim_type_stats:
        print(f"  {stat['claim_type']}: {stat['count']}")
    
    # By severity
    severity_stats = Claim.objects.values('severity').annotate(count=Count('id'))
    print("\nBy Severity:")
    for stat in severity_stats:
        print(f"  {stat['severity']}: {stat['count']}")
    
    # Financial metrics
    total_claimed = Claim.objects.aggregate(total=Sum('claimed_amount'))['total'] or 0
    total_approved = Claim.objects.aggregate(total=Sum('approved_amount'))['total'] or 0
    total_paid = Claim.objects.aggregate(total=Sum('paid_amount'))['total'] or 0
    avg_claim = Claim.objects.aggregate(avg=Avg('claimed_amount'))['avg'] or 0
    avg_fraud_score = Claim.objects.aggregate(avg=Avg('fraud_score'))['avg'] or 0
    
    print(f"\nTotal Claimed Amount: ${total_claimed:,.2f}")
    print(f"Total Approved Amount: ${total_approved:,.2f}")
    print(f"Total Paid Amount: ${total_paid:,.2f}")
    print(f"Average Claim Amount: ${avg_claim:,.2f}")
    print(f"Average Fraud Score: {avg_fraud_score:.3f}")
    
    # Fraud detection metrics
    high_risk_claims = Claim.objects.filter(fraud_score__gte=0.7).count()
    print(f"\nHigh Risk Claims (score ≥ 0.7): {high_risk_claims}")
    
    print("\n" + "="*70)
    print("✅ STATISTICS COMPLETE")
    print("="*70 + "\n")


if __name__ == '__main__':
    print_statistics()