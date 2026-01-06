"""
Simple API test script
Run with: python test_api.py
"""

import requests
import json

BASE_URL = 'http://127.0.0.1:8000/api'

def test_register():
    """Test user registration"""
    url = f'{BASE_URL}/dashboard/auth/register/'
    data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpass123',
        'first_name': 'Test',
        'last_name': 'User'
    }
    
    response = requests.post(url, json=data)
    print(f"Registration Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")
    
    return response.json().get('tokens', {}).get('access')

def test_login():
    """Test user login"""
    url = f'{BASE_URL}/dashboard/auth/login/'
    data = {
        'username': 'testuser',
        'password': 'testpass123'
    }
    
    response = requests.post(url, json=data)
    print(f"Login Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")
    
    return response.json().get('tokens', {}).get('access')

def test_dashboard_stats(token):
    """Test dashboard statistics endpoint"""
    url = f'{BASE_URL}/dashboard/statistics/'
    headers = {'Authorization': f'Bearer {token}'}
    
    response = requests.get(url, headers=headers)
    print(f"Dashboard Stats Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")

if __name__ == '__main__':
    print("=" * 50)
    print("API ENDPOINT TESTING")
    print("=" * 50 + "\n")
    
    print("Make sure Django server is running on port 8000\n")
    
    try:
        # Test registration
        token = test_register()
        
        # If registration fails (user exists), try login
        if not token:
            token = test_login()
        
        # Test protected endpoint
        if token:
            test_dashboard_stats(token)
            
        print("=" * 50)
        print("All tests completed!")
        print("=" * 50)
        
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to server. Make sure Django is running on port 8000")
    except Exception as e:
        print(f"ERROR: {str(e)}")