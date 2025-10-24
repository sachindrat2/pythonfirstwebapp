#!/usr/bin/env python3
"""Test the admin login and dashboard flow"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_admin_flow():
    print("🧪 Testing Admin Login Flow")
    print("=" * 50)
    
    # Test 1: Check if admin login page loads
    print("1. Testing admin login page...")
    try:
        response = requests.get(f"{BASE_URL}/admin/login")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Admin login page loads successfully")
        else:
            print("   ❌ Admin login page failed to load")
            return
    except Exception as e:
        print(f"   ❌ Error accessing admin login: {e}")
        return
    
    # Test 2: Test admin login POST
    print("\n2. Testing admin login POST...")
    try:
        login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        response = requests.post(f"{BASE_URL}/admin/login", data=login_data)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ Login successful!")
            print(f"   Token: {result.get('access_token', 'Not found')[:50]}...")
            print(f"   Redirect: {result.get('redirect', 'Not found')}")
            
            # Extract token for dashboard test
            token = result.get('access_token')
            
            # Test 3: Access dashboard with cookie
            print("\n3. Testing dashboard access...")
            cookies = response.cookies
            dashboard_response = requests.get(f"{BASE_URL}/admin/dashboard", cookies=cookies)
            print(f"   Status: {dashboard_response.status_code}")
            
            if dashboard_response.status_code == 200:
                print("   ✅ Dashboard loads successfully!")
                print(f"   Content length: {len(dashboard_response.text)} characters")
                if "3D Dashboard" in dashboard_response.text:
                    print("   ✅ 3D Dashboard content found!")
                else:
                    print("   ⚠️  3D Dashboard content not found in response")
            else:
                print(f"   ❌ Dashboard failed to load: {dashboard_response.status_code}")
                print(f"   Response: {dashboard_response.text[:200]}...")
                
        else:
            print(f"   ❌ Login failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error during login: {e}")

if __name__ == "__main__":
    test_admin_flow()