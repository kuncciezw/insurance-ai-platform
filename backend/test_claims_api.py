"""
Test Script for Claims Automation API
Tests all endpoints for claim cost estimation and automated processing
"""

import os
import sys
import django
import requests
import json
from decimal import Decimal
from datetime import datetime

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.fraud_detection.models import Claim, Policyholder, Vehicle, Policy
from apps.claims_automation.models import ClaimEstimate, ClaimProcessingLog


# API Configuration
BASE_URL = 'http://localhost:8000/api'
USERNAME = 'insurance_admin'
PASSWORD = 'admin'


class ClaimsAPITester:
    """Test Claims Automation API endpoints"""
    
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.headers = {'Content-Type': 'application/json'}
    
    def print_section(self, title):
        """Print section header"""
        print("\n" + "=" * 80)
        print(f"  {title}")
        print("=" * 80)
    
    def print_result(self, success, message):
        """Print test result"""
        status = "✓" if success else "✗"
        print(f"{status} {message}")
    
    def login(self):
        """Login and get JWT token"""
        self.print_section("AUTHENTICATION")
        
        response = requests.post(
            f"{self.base_url}/dashboard/auth/login/",
            json={'username': USERNAME, 'password': PASSWORD}
        )
        
        if response.status_code == 200:
            data = response.json()
            # FIX: Access token from nested structure
            self.token = data['tokens']['access']
            self.headers['Authorization'] = f'Bearer {self.token}'
            self.print_result(True, f"Login successful for user: {data['user']['username']}")
            return True
        else:
            self.print_result(False, f"Login failed: {response.text}")
            return False
    
    def test_estimate_cost(self):
        """Test: Estimate claim cost"""
        self.print_section("TEST: Estimate Claim Cost")
        
        # Get a claim without estimate
        claims = Claim.objects.exclude(
            id__in=ClaimEstimate.objects.values_list('claim_id', flat=True)
        )[:1]
        
        if not claims:
            print("⚠️  No claims available without estimates")
            return False
        
        claim = claims[0]
        
        print(f"\nTesting with Claim: {claim.claim_number}")
        print(f"  - Type: {claim.claim_type}")
        print(f"  - Severity: {claim.severity}")
        print(f"  - Claimed Amount: ${claim.claimed_amount}")
        
        data = {
            'claim_id': str(claim.id)
        }
        
        response = requests.post(
            f"{self.base_url}/claims-automation/estimate-cost/",
            headers=self.headers,
            json=data
        )
        
        if response.status_code == 201:
            result = response.json()
            estimate = result['estimate']
            
            print("\nEstimate Generated:")
            print(f"  - Estimate Number: {estimate['estimate_number']}")
            print(f"  - Estimated Cost: ${float(estimate['estimated_cost']):,.2f}")
            print(f"  - Confidence Score: {float(estimate['confidence_score']) * 100:.1f}%")
            print(f"  - Predicted Severity: {estimate['predicted_severity']}")
            print(f"  - Triage Priority: {estimate['triage_priority']}")
            print(f"  - Processing Recommendation: {estimate['processing_recommendation']}")
            print(f"  - Recommended Reserve: ${float(estimate['recommended_reserve']):,.2f}")
            print(f"  - Processing Time: {result['processing_time_ms']} ms")
            
            self.print_result(True, "Cost estimate generated successfully")
            return estimate['id']
        else:
            self.print_result(False, f"Failed: {response.text}")
            return None
    
    def test_batch_triage(self):
        """Test: Batch triage claims"""
        self.print_section("TEST: Batch Triage Claims")
        
        # Get multiple claims
        claims = Claim.objects.all()[:5]
        
        if not claims:
            print("⚠️  No claims available for triage")
            return False
        
        claim_ids = [str(claim.id) for claim in claims]
        
        print(f"\nTriaging {len(claim_ids)} claims...")
        
        data = {
            'claim_ids': claim_ids
        }
        
        response = requests.post(
            f"{self.base_url}/claims-automation/batch-triage/",
            headers=self.headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print("\nTriage Results:")
            print(f"  - Total Claims: {result['summary']['total']}")
            print(f"  - Triaged: {result['summary']['triaged']}")
            print(f"  - Existing Estimates: {result['summary']['existing']}")
            print(f"  - Errors: {result['summary']['errors']}")
            
            print("\nIndividual Results:")
            for item in result['results'][:3]:  # Show first 3
                print(f"\n  Claim {item['claim_number']}:")
                print(f"    - Status: {item['status']}")
                if 'estimated_cost' in item:
                    print(f"    - Estimated Cost: ${item['estimated_cost']:,.2f}")
                if 'triage_priority' in item:
                    print(f"    - Priority: {item['triage_priority']}")
            
            self.print_result(True, f"Successfully triaged {len(claim_ids)} claims")
            return True
        else:
            self.print_result(False, f"Failed: {response.text}")
            return False
    
    def test_processing_recommendations(self):
        """Test: Get processing recommendations"""
        self.print_section("TEST: Processing Recommendations")
        
        # Get a claim with estimate
        estimate = ClaimEstimate.objects.first()
        
        if not estimate:
            print("⚠️  No estimates available")
            return False
        
        claim = estimate.claim
        
        print(f"\nGetting recommendations for: {claim.claim_number}")
        
        response = requests.get(
            f"{self.base_url}/claims-automation/recommendations/{claim.id}/",
            headers=self.headers
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print("\nRecommendations:")
            print(f"  - Claim Number: {result['claim_number']}")
            print(f"  - Estimated Cost: ${result['estimated_cost']:,.2f}")
            print(f"  - Recommended Reserve: ${result['recommended_reserve']:,.2f}")
            print(f"  - Processing Recommendation: {result['processing_recommendation']}")
            print(f"  - Triage Priority: {result['triage_priority']}")
            print(f"  - Estimated Processing Days: {result['estimated_processing_days']}")
            
            print("\nRecommended Actions:")
            for i, action in enumerate(result['actions'], 1):
                print(f"\n  {i}. {action['action']}")
                print(f"     Reason: {action['reason']}")
                print(f"     Priority: {action['priority']}")
            
            print("\nReserve Action:")
            reserve = result['reserve_action']
            print(f"  - Recommended Reserve: ${reserve['recommended_reserve']:,.2f}")
            print(f"  - Action: {reserve['action']}")
            
            self.print_result(True, "Recommendations generated successfully")
            return True
        else:
            self.print_result(False, f"Failed: {response.text}")
            return False
    
    def test_list_estimates(self):
        """Test: List claim estimates"""
        self.print_section("TEST: List Claim Estimates")
        
        response = requests.get(
            f"{self.base_url}/claims-automation/estimates/",
            headers=self.headers
        )
        
        if response.status_code == 200:
            data = response.json()
            # Handle both list and paginated response
            estimates = data if isinstance(data, list) else data.get('results', [])
            
            print(f"\nFound {len(estimates)} estimates")
            
            # Show first 3
            for estimate in estimates[:3]:
                print(f"\n  {estimate['estimate_number']}:")
                print(f"    - Claim: {estimate['claim_number']}")
                print(f"    - Estimated Cost: ${float(estimate['estimated_cost']):,.2f}")
                print(f"    - Severity: {estimate['predicted_severity']}")
                print(f"    - Priority: {estimate['triage_priority']}")
                print(f"    - Needs Review: {estimate['needs_review']}")
            
            self.print_result(True, f"Listed {len(estimates)} estimates")
            return True
        else:
            self.print_result(False, f"Failed: {response.text}")
            return False
    
    def test_filter_estimates(self):
        """Test: Filter estimates by severity"""
        self.print_section("TEST: Filter Estimates by Severity")
        
        severity = 'MAJOR'
        
        response = requests.get(
            f"{self.base_url}/claims-automation/estimates/?severity={severity}",
            headers=self.headers
        )
        
        if response.status_code == 200:
            data = response.json()
            # Handle both list and paginated response
            estimates = data if isinstance(data, list) else data.get('results', [])
            
            print(f"\nFound {len(estimates)} {severity} severity estimates")
            
            for estimate in estimates[:3]:
                print(f"\n  {estimate['estimate_number']}:")
                print(f"    - Estimated Cost: ${float(estimate['estimated_cost']):,.2f}")
                print(f"    - Priority: {estimate['triage_priority']}")
            
            self.print_result(True, f"Filtered by severity: {severity}")
            return True
        else:
            self.print_result(False, f"Failed: {response.text}")
            return False
    
    def test_update_actual_settlement(self):
        """Test: Update estimate with actual settlement"""
        self.print_section("TEST: Update Actual Settlement")
        
        # Get an estimate without actual settlement
        estimate = ClaimEstimate.objects.filter(
            actual_settlement_amount__isnull=True
        ).first()
        
        if not estimate:
            print("⚠️  No estimates available without actual settlement")
            return False
        
        print(f"\nUpdating estimate: {estimate.estimate_number}")
        print(f"  - Estimated Cost: ${estimate.estimated_cost}")
        
        # Set actual settlement slightly different from estimate
        # IMPORTANT: Round to 2 decimal places to avoid validation error
        actual_amount = round(float(estimate.estimated_cost) * 1.05, 2)
        
        data = {
            'actual_settlement_amount': actual_amount,
            'notes': 'Test settlement update'
        }
        
        response = requests.post(
            f"{self.base_url}/claims-automation/estimates/{estimate.id}/update_actual_settlement/",
            headers=self.headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print("\nSettlement Updated:")
            print(f"  - Actual Amount: ${actual_amount:,.2f}")
            print(f"  - Variance: {result['variance_percentage']:.2f}%")
            print(f"  - Within Tolerance: {result['is_within_tolerance']}")
            print(f"  - Prediction Accuracy: {result['prediction_accuracy']:.2f}%")
            
            self.print_result(True, "Actual settlement updated successfully")
            return True
        else:
            self.print_result(False, f"Failed: {response.text}")
            return False
    
    def test_processing_logs(self):
        """Test: View processing logs"""
        self.print_section("TEST: Processing Logs")
        
        response = requests.get(
            f"{self.base_url}/claims-automation/processing-logs/",
            headers=self.headers
        )
        
        if response.status_code == 200:
            data = response.json()
            # Handle both list and paginated response
            logs = data if isinstance(data, list) else data.get('results', [])
            
            print(f"\nFound {len(logs)} processing logs")
            
            # Show recent logs
            for log in logs[:5]:
                print(f"\n  {log['created_at']}:")
                print(f"    - Claim: {log['claim_number']}")
                print(f"    - Action: {log['action_type']}")
                print(f"    - Automated: {log['is_automated']}")
                print(f"    - Performed By: {log['performed_by']}")
            
            self.print_result(True, f"Listed {len(logs)} processing logs")
            return True
        else:
            self.print_result(False, f"Failed: {response.text}")
            return False
    
    def test_claims_statistics(self):
        """Test: Claims automation statistics"""
        self.print_section("TEST: Claims Statistics")
        
        response = requests.get(
            f"{self.base_url}/claims-automation/statistics/",
            headers=self.headers
        )
        
        if response.status_code == 200:
            stats = response.json()
            
            print("\nClaims Automation Statistics:")
            print(f"  - Total Estimates: {stats['total_estimates']}")
            
            print("\nBy Severity:")
            for severity, data in stats['by_severity'].items():
                print(f"  - {severity}: {data['count']} claims (Avg: ${data['avg_cost']:,.2f})")
            
            print("\nBy Priority:")
            for priority, count in stats['by_priority'].items():
                print(f"  - {priority}: {count}")
            
            print("\nBy Recommendation:")
            for rec, count in stats['by_recommendation'].items():
                print(f"  - {rec}: {count}")
            
            print("\nAccuracy Statistics:")
            acc = stats['accuracy_statistics']
            print(f"  - Total Validated: {acc['total_validated']}")
            print(f"  - Average Accuracy: {acc['avg_accuracy']:.2f}%")
            print(f"  - Within Tolerance: {acc['within_tolerance']}")
            
            print("\nProcessing Logs:")
            logs = stats['processing_logs']
            print(f"  - Total: {logs['total']}")
            print(f"  - Automated: {logs['automated']}")
            print(f"  - Manual: {logs['manual']}")
            
            print("\nAverage Costs:")
            costs = stats['average_costs']
            print(f"  - Estimated Cost: ${costs['estimated_cost']:,.2f}")
            print(f"  - Recommended Reserve: ${costs['recommended_reserve']:,.2f}")
            
            self.print_result(True, "Statistics retrieved successfully")
            return True
        else:
            self.print_result(False, f"Failed: {response.text}")
            return False
    
    def test_database_integrity(self):
        """Test database integrity"""
        self.print_section("DATABASE INTEGRITY CHECK")
        
        estimates_count = ClaimEstimate.objects.count()
        logs_count = ClaimProcessingLog.objects.count()
        claims_count = Claim.objects.count()
        
        print(f"\nDatabase Counts:")
        print(f"  - Total Claims: {claims_count}")
        print(f"  - Total Estimates: {estimates_count}")
        print(f"  - Total Processing Logs: {logs_count}")
        
        # Check for estimates without claims
        orphaned = ClaimEstimate.objects.filter(claim__isnull=True).count()
        print(f"  - Orphaned Estimates: {orphaned}")
        
        # Check severity distribution
        print("\nSeverity Distribution:")
        for severity in ['MINOR', 'MODERATE', 'MAJOR', 'CRITICAL']:
            count = ClaimEstimate.objects.filter(predicted_severity=severity).count()
            percentage = (count / estimates_count * 100) if estimates_count > 0 else 0
            print(f"  - {severity}: {count} ({percentage:.1f}%)")
        
        # Check priority distribution
        print("\nPriority Distribution:")
        for priority in ['LOW', 'MEDIUM', 'HIGH', 'URGENT']:
            count = ClaimEstimate.objects.filter(triage_priority=priority).count()
            percentage = (count / estimates_count * 100) if estimates_count > 0 else 0
            print(f"  - {priority}: {count} ({percentage:.1f}%)")
        
        self.print_result(True, "Database integrity check complete")
        return True
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "=" * 80)
        print("  CLAIMS AUTOMATION API TEST SUITE")
        print("=" * 80)
        print(f"  Base URL: {self.base_url}")
        print(f"  Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Login
        if not self.login():
            print("\n❌ Login failed. Cannot proceed with tests.")
            return
        
        # Run tests
        tests = [
            ('Estimate Cost', self.test_estimate_cost),
            ('Batch Triage', self.test_batch_triage),
            ('Processing Recommendations', self.test_processing_recommendations),
            ('List Estimates', self.test_list_estimates),
            ('Filter Estimates', self.test_filter_estimates),
            ('Update Settlement', self.test_update_actual_settlement),
            ('Processing Logs', self.test_processing_logs),
            ('Statistics', self.test_claims_statistics),
            ('Database Integrity', self.test_database_integrity),
        ]
        
        results = []
        for name, test_func in tests:
            try:
                result = test_func()
                results.append((name, result))
            except Exception as e:
                print(f"\n❌ Error in {name}: {str(e)}")
                results.append((name, False))
        
        # Summary
        self.print_section("TEST SUMMARY")
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        print(f"\nResults: {passed}/{total} tests passed")
        print("\nDetailed Results:")
        for name, result in results:
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"  {status}: {name}")
        
        if passed == total:
            print("\n🎉 All tests passed!")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed")
        
        print("\n" + "=" * 80)


if __name__ == '__main__':
    tester = ClaimsAPITester()
    tester.run_all_tests()