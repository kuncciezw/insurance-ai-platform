"""
Test Fraud Detection API Endpoints
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000/api"
USERNAME = "insurance_admin" 
PASSWORD = "admin" 


def print_header(title):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def print_response(response):
    """Print formatted response"""
    print(f"\nStatus Code: {response.status_code}")
    try:
        data = response.json()
        print(json.dumps(data, indent=2))
    except:
        print(response.text)


def get_auth_token():
    """Get JWT authentication token"""
    print_header("AUTHENTICATING")
    
    url = f"{BASE_URL}/dashboard/auth/login/"
    data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            # Fixed: Access token from nested 'tokens' object
            token = response_data['tokens']['access']
            print("✓ Authentication successful")
            print(f"  User: {response_data['user']['username']}")
            return token
        else:
            print("✗ Authentication failed")
            print_response(response)
            return None
    except KeyError as e:
        print(f"✗ Unexpected response format. Missing key: {e}")
        print("Response data:")
        print_response(response)
        return None
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to server. Is the Django server running?")
        print(f"  Please start server with: python manage.py runserver")
        return None
    except Exception as e:
        print(f"✗ Unexpected error during authentication: {e}")
        return None


def test_analyze_single_claim(token, claim_id):
    """Test single claim fraud analysis"""
    print_header(f"TEST 1: ANALYZE SINGLE CLAIM (ID: {claim_id})")
    
    url = f"{BASE_URL}/fraud-detection/fraud/analyze-claim/"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"claim_id": claim_id}
    
    try:
        response = requests.post(url, json=data, headers=headers)
        print_response(response)
        
        if response.status_code == 200:
            result = response.json()
            print("\n✓ Fraud Analysis Summary:")
            print(f"  • Fraud Probability: {result['fraud_analysis']['fraud_probability']*100:.2f}%")
            print(f"  • Risk Level: {result['fraud_analysis']['risk_level']}")
            print(f"  • Recommendation: {result['recommendation']}")
            print(f"  • Automated Action: {result['automated_action']}")
            return True
        else:
            print(f"✗ Test failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Test error: {e}")
        return False


def test_batch_analyze_pending(token):
    """Test batch analysis of pending claims"""
    print_header("TEST 2: BATCH ANALYZE PENDING CLAIMS")
    
    url = f"{BASE_URL}/fraud-detection/fraud/batch-analyze/"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"filter": "all_pending"}
    
    try:
        response = requests.post(url, json=data, headers=headers)
        print_response(response)
        
        if response.status_code == 200:
            result = response.json()
            print("\n✓ Batch Analysis Summary:")
            print(f"  • Total Analyzed: {result['total_analyzed']}")
            print(f"  • High Risk: {result['high_risk_count']}")
            print(f"  • Medium Risk: {result['medium_risk_count']}")
            print(f"  • Low Risk: {result['low_risk_count']}")
            return True
        else:
            print(f"✗ Test failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Test error: {e}")
        return False


def test_batch_analyze_specific_claims(token, claim_ids):
    """Test batch analysis of specific claims"""
    print_header(f"TEST 3: BATCH ANALYZE SPECIFIC CLAIMS")
    
    url = f"{BASE_URL}/fraud-detection/fraud/batch-analyze/"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"claim_ids": claim_ids}
    
    try:
        response = requests.post(url, json=data, headers=headers)
        print_response(response)
        
        if response.status_code == 200:
            print("✓ Specific claims analyzed successfully")
            return True
        else:
            print(f"✗ Test failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Test error: {e}")
        return False


def test_high_risk_claims(token):
    """Test getting high-risk claims"""
    print_header("TEST 4: GET HIGH-RISK CLAIMS")
    
    url = f"{BASE_URL}/fraud-detection/fraud/high-risk-claims/?threshold=0.5&limit=10"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        print_response(response)
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✓ Found {result['count']} high-risk claims")
            return True
        else:
            print(f"✗ Test failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Test error: {e}")
        return False


def test_fraud_statistics(token):
    """Test fraud statistics endpoint"""
    print_header("TEST 5: GET FRAUD STATISTICS")
    
    url = f"{BASE_URL}/fraud-detection/fraud/statistics/"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        print_response(response)
        
        if response.status_code == 200:
            result = response.json()
            print("\n✓ Statistics Summary:")
            print(f"  • Total Claims: {result['total_claims']}")
            print(f"  • Fraudulent Claims: {result['fraudulent_claims']}")
            print(f"  • Fraud Rate: {result['fraud_rate']*100:.2f}%")
            print(f"  • Average Fraud Score: {result['average_fraud_score']:.4f}")
            return True
        else:
            print(f"✗ Test failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Test error: {e}")
        return False


def get_sample_claim_id(token):
    """Get a sample claim ID for testing"""
    url = f"{BASE_URL}/fraud-detection/claims/"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            claims = response.json()
            # Handle both paginated and non-paginated responses
            if isinstance(claims, dict) and 'results' in claims:
                if claims['results']:
                    return claims['results'][0]['id']
            elif isinstance(claims, list) and claims:
                return claims[0]['id']
        
        return None
    except Exception as e:
        print(f"Warning: Error fetching sample claim: {e}")
        return None


def test_dashboard_stats(token):
    """Test dashboard statistics endpoint"""
    print_header("BONUS TEST: DASHBOARD STATISTICS")
    
    url = f"{BASE_URL}/dashboard/statistics/"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            stats = response.json()
            print("✓ Dashboard statistics retrieved successfully")
            print(f"\n  • Total Policyholders: {stats['policyholders']['total']}")
            print(f"  • Total Claims: {stats['claims']['total']}")
            print(f"  • Fraudulent Claims: {stats['claims']['fraudulent']}")
            print(f"  • Fraud Detection Rate: {stats['claims']['fraud_detection_rate']}%")
            return True
        else:
            print(f"✗ Failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    """Run all fraud detection API tests"""
    print_header("FRAUD DETECTION API TEST SUITE")
    print(f"Testing API at: {BASE_URL}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get authentication token
    token = get_auth_token()
    if not token:
        print("\n✗ Cannot proceed without authentication")
        print("\nTroubleshooting steps:")
        print("1. Ensure Django server is running: python manage.py runserver")
        print("2. Check if USERNAME and PASSWORD are correct")
        print("3. Verify the API endpoint URL is correct")
        return
    
    # Test dashboard stats first (doesn't require claims)
    print("\nTesting dashboard endpoint...")
    test_dashboard_stats(token)
    
    # Get a sample claim ID
    print("\nFetching sample claim ID...")
    claim_id = get_sample_claim_id(token)
    
    if not claim_id:
        print("⚠️  No claims found in database.")
        print("\nTo generate test data, run:")
        print("  python manage.py generate_data")
        print("\nSkipping claim-specific tests...")
        
        # Only run tests that don't require claims
        results = {
            'dashboard_stats': test_dashboard_stats(token),
            'fraud_statistics': test_fraud_statistics(token),
        }
    else:
        print(f"✓ Using claim ID: {claim_id} for testing")
        
        # Run all tests
        results = {
            'dashboard_stats': test_dashboard_stats(token),
            'analyze_single': test_analyze_single_claim(token, claim_id),
            'batch_pending': test_batch_analyze_pending(token),
            'batch_specific': test_batch_analyze_specific_claims(token, [claim_id]),
            'high_risk': test_high_risk_claims(token),
            'statistics': test_fraud_statistics(token),
        }
    
    # Print summary
    print_header("TEST SUMMARY")
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    print(f"\nResults: {passed}/{total} tests passed")
    print("\nDetailed Results:")
    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"  {test_name}: {status}")
    
    if passed == total:
        print("\n" + "="*70)
        print("  🎉 ALL TESTS PASSED!")
        print("="*70)
    else:
        print("\n" + "="*70)
        print("  ⚠️  SOME TESTS FAILED - CHECK ERRORS ABOVE")
        print("="*70)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()