#!/usr/bin/env python3
"""
Test script to check Azure deployment status
"""
import requests
import time

def test_azure_deployment():
    """Test if the Azure app is responding"""
    azure_url = "https://ownnoteapp-hedxcahwcrhwb8hb.canadacentral-01.azurewebsites.net"
    
    print("🔍 Testing Azure deployment...")
    print(f"URL: {azure_url}")
    
    try:
        # Test main endpoint
        print("\n1. Testing main endpoint...")
        response = requests.get(azure_url, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Main endpoint is working!")
        else:
            print(f"⚠️ Main endpoint returned status {response.status_code}")
            
        # Test health check
        print("\n2. Testing health endpoint...")
        health_response = requests.get(f"{azure_url}/health", timeout=30)
        print(f"Health Status: {health_response.status_code}")
        
        # Test admin test endpoint
        print("\n3. Testing admin test endpoint...")
        admin_test_response = requests.get(f"{azure_url}/admin/test", timeout=30)
        print(f"Admin Test Status: {admin_test_response.status_code}")
        
        if admin_test_response.status_code == 200:
            print("✅ Admin routes are working!")
            print(f"Response: {admin_test_response.json()}")
        else:
            print(f"⚠️ Admin test returned status {admin_test_response.status_code}")
        
        # Test diagnostic routes
        print("\n4. Testing diagnostic route /test-admin...")
        test_admin_response = requests.get(f"{azure_url}/test-admin", timeout=30)
        print(f"Test Admin Status: {test_admin_response.status_code}")
        
        if test_admin_response.status_code == 200:
            print("✅ /test-admin works!")
            print(f"Response: {test_admin_response.json()}")
        else:
            print(f"⚠️ /test-admin returned status {test_admin_response.status_code}")
        
        print("\n5. Testing alternative admin login /adminlogin...")
        alt_admin_response = requests.get(f"{azure_url}/adminlogin", timeout=30)
        print(f"Alternative Admin Login Status: {alt_admin_response.status_code}")
        
        if alt_admin_response.status_code == 200:
            print("✅ Alternative admin login works!")
        else:
            print(f"⚠️ Alternative admin login returned status {alt_admin_response.status_code}")
        
        # Test admin login
        print("\n6. Testing original admin login /admin/login...")
        admin_response = requests.get(f"{azure_url}/admin/login", timeout=30)
        print(f"Admin Login Status: {admin_response.status_code}")
        
        if admin_response.status_code == 200:
            print("✅ Admin login page is accessible!")
        else:
            print(f"⚠️ Admin login returned status {admin_response.status_code}")
            if admin_response.status_code == 405:
                print("💡 405 Method Not Allowed - This might be a routing issue")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - App might be starting up or down")
        print("💡 This could mean:")
        print("   - Deployment is still in progress")
        print("   - App Service is cold starting") 
        print("   - There's a configuration issue")
        
    except requests.exceptions.Timeout:
        print("⏰ Request timed out - App might be slow to respond")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_azure_deployment()