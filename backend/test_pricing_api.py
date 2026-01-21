"""
Test Dynamic Pricing API Endpoints
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
        
        if response.status_code == 200:
            response_data = response.json()
            token = response_data['tokens']['access']
            print("✓ Authentication successful")
            print(f"  User: {response_data['user']['username']}")
            return token
        else:
            print("✗ Authentication failed")
            print_response(response)
            return None
    except Exception as e:
        print(f"✗ Authentication error: {e}")
        return None


def get_sample_policyholder(token):
    """Get a sample policyholder ID"""
    url = f"{BASE_URL}/fraud-detection/policyholders/"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get('results'):
                return data['results'][0]['id']
    except:
        pass
    return None


def get_sample_vehicle(token):
    """Get a sample vehicle ID"""
    url = f"{BASE_URL}/fraud-detection/vehicles/"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get('results'):
                return data['results'][0]['id']
    except:
        pass
    return None


def test_calculate_premium_existing(token, policyholder_id, vehicle_id):
    """Test premium calculation with existing customer and vehicle"""
    print_header("TEST 1: CALCULATE PREMIUM (EXISTING CUSTOMER & VEHICLE)")
    
    url = f"{BASE_URL}/dynamic-pricing/calculate-premium/"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "policy_type": "COMPREHENSIVE",
        "coverage_level": "STANDARD",
        "coverage_amount": 50000,
        "deductible": 1000,
        "policyholder_id": policyholder_id,
        "vehicle_id": vehicle_id,
        "has_roadside_assistance": True,
        "has_rental_coverage": False,
        "has_glass_coverage": True
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        print_response(response)
        
        if response.status_code == 200:
            result = response.json()
            print("\n✓ Premium Calculation Summary:")
            print(f"  • Base Premium: ${result['base_premium']:.2f}")
            print(f"  • Risk Adjustment: ${result['risk_adjustment']:.2f}")
            print(f"  • Discount: ${result['discount_amount']:.2f}")
            print(f"  • Final Premium: ${result['final_premium']:.2f}")
            print(f"  • ML Predicted: ${result['ml_predicted_premium']:.2f}")
            print(f"  • Confidence: {result['confidence_score']*100:.1f}%")
            return True, result['final_premium']
        else:
            print("✗ Test failed")
            return False, None
    except Exception as e:
        print(f"✗ Test error: {e}")
        return False, None


def test_calculate_premium_new(token):
    """Test premium calculation with new customer data"""
    print_header("TEST 2: CALCULATE PREMIUM (NEW CUSTOMER)")
    
    url = f"{BASE_URL}/dynamic-pricing/calculate-premium/"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "policy_type": "COMPREHENSIVE",
        "coverage_level": "PREMIUM",
        "coverage_amount": 75000,
        "deductible": 500,
        "customer_age": 28,
        "customer_credit_score": 720,
        "customer_years_experience": 3,
        "vehicle_year": 2020,
        "vehicle_make": "Toyota",
        "vehicle_model": "Camry",
        "vehicle_value": 25000,
        "vehicle_has_anti_theft": True,
        "vehicle_is_modified": False,
        "has_roadside_assistance": False,
        "has_rental_coverage": True,
        "has_glass_coverage": False
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        print_response(response)
        
        if response.status_code == 200:
            result = response.json()
            print("\n✓ Premium calculated for new customer")
            print(f"  • Final Premium: ${result['final_premium']:.2f}")
            return True
        else:
            print("✗ Test failed")
            return False
    except Exception as e:
        print(f"✗ Test error: {e}")
        return False


def test_generate_quote(token, policyholder_id, vehicle_id):
    """Test quote generation"""
    print_header("TEST 3: GENERATE QUOTE")
    
    url = f"{BASE_URL}/dynamic-pricing/generate-quote/"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "policy_type": "COMPREHENSIVE",
        "coverage_level": "STANDARD",
        "coverage_amount": 60000,
        "deductible": 1500,
        "policyholder_id": policyholder_id,
        "vehicle_id": vehicle_id,
        "has_roadside_assistance": True,
        "has_rental_coverage": True,
        "has_glass_coverage": True,
        "customer_email": "test@example.com",
        "customer_phone": "+263771234567"
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        print_response(response)
        
        if response.status_code == 201:
            result = response.json()
            print("\n✓ Quote Generated Successfully:")
            print(f"  • Quote Number: {result['quote']['quote_number']}")
            print(f"  • Final Premium: ${result['quote']['final_premium']}")
            print(f"  • Status: {result['quote']['status']}")
            print(f"  • Valid Until: {result['quote']['valid_until']}")
            return True, result['quote']['id']
        else:
            print("✗ Test failed")
            return False, None
    except Exception as e:
        print(f"✗ Test error: {e}")
        return False, None


def test_compare_prices(token, policyholder_id, vehicle_id):
    """Test price comparison across coverage levels"""
    print_header("TEST 4: COMPARE PRICES")
    
    url = f"{BASE_URL}/dynamic-pricing/compare-prices/"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "policy_type": "COMPREHENSIVE",
        "coverage_amount": 50000,
        "deductible": 1000,
        "policyholder_id": policyholder_id,
        "vehicle_id": vehicle_id,
        "has_roadside_assistance": False,
        "has_rental_coverage": False,
        "has_glass_coverage": False
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        print_response(response)
        
        if response.status_code == 200:
            result = response.json()
            print("\n✓ Price Comparison:")
            for comp in result['comparisons']:
                print(f"\n  {comp['coverage_level']}:")
                print(f"    • Coverage: ${comp['coverage_amount']:,.2f}")
                print(f"    • Premium: ${comp['final_premium']:,.2f}")
                if 'savings_vs_standard' in comp:
                    savings = comp['savings_vs_standard']
                    if savings > 0:
                        print(f"    • Savings: ${savings:,.2f}")
                    elif savings < 0:
                        print(f"    • Additional Cost: ${abs(savings):,.2f}")
            return True
        else:
            print("✗ Test failed")
            return False
    except Exception as e:
        print(f"✗ Test error: {e}")
        return False


def test_list_quotes(token):
    """Test listing quotes"""
    print_header("TEST 5: LIST QUOTES")
    
    url = f"{BASE_URL}/dynamic-pricing/quotes/"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        print_response(response)
        
        if response.status_code == 200:
            result = response.json()
            count = result.get('count', len(result))
            print(f"\n✓ Found {count} quotes")
            return True
        else:
            print("✗ Test failed")
            return False
    except Exception as e:
        print(f"✗ Test error: {e}")
        return False


def test_pricing_statistics(token):
    """Test pricing statistics endpoint"""
    print_header("TEST 6: PRICING STATISTICS")
    
    url = f"{BASE_URL}/dynamic-pricing/statistics/"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        print_response(response)
        
        if response.status_code == 200:
            result = response.json()
            print("\n✓ Statistics Summary:")
            print(f"  • Total Quotes: {result['total_quotes']}")
            print(f"  • Active Quotes: {result['active_quotes']}")
            print(f"  • Accepted Quotes: {result['accepted_quotes']}")
            print(f"  • Conversion Rate: {result['conversion_rate']}%")
            print(f"  • Average Premium: ${result['average_premium']:.2f}")
            return True
        else:
            print("✗ Test failed")
            return False
    except Exception as e:
        print(f"✗ Test error: {e}")
        return False


def main():
    """Run all dynamic pricing API tests"""
    print_header("DYNAMIC PRICING API TEST SUITE")
    print(f"Testing API at: {BASE_URL}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get authentication token
    token = get_auth_token()
    if not token:
        print("\n✗ Cannot proceed without authentication")
        return
    
    # Get sample data
    print("\nFetching sample policyholder and vehicle...")
    policyholder_id = get_sample_policyholder(token)
    vehicle_id = get_sample_vehicle(token)
    
    if not policyholder_id or not vehicle_id:
        print("⚠️  No policyholder or vehicle found.")
        print("\nTo generate test data, run:")
        print("  python manage.py generate_data")
        print("\nRunning limited tests...")
        
        results = {
            'statistics': test_pricing_statistics(token),
        }
    else:
        print(f"✓ Using Policyholder ID: {policyholder_id}")
        print(f"✓ Using Vehicle ID: {vehicle_id}")
        
        # Run all tests
        results = {
            'calculate_existing': test_calculate_premium_existing(token, policyholder_id, vehicle_id)[0],
            'calculate_new': test_calculate_premium_new(token),
            'generate_quote': test_generate_quote(token, policyholder_id, vehicle_id)[0],
            'compare_prices': test_compare_prices(token, policyholder_id, vehicle_id),
            'list_quotes': test_list_quotes(token),
            'statistics': test_pricing_statistics(token),
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
        print("  🎉 ALL DYNAMIC PRICING API TESTS PASSED!")
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