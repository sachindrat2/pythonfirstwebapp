#!/usr/bin/env python3
"""
Test which version is deployed on Azure
"""
import requests
import json

def check_azure_version():
    """Check if Azure has the latest version"""
    azure_url = "https://ownnoteapp-hedxcahwcrhwb8hb.canadacentral-01.azurewebsites.net"
    
    print("🔍 Checking Azure deployment version...")
    
    try:
        # Check health endpoint for version
        print("\n1. Checking health endpoint...")
        health_response = requests.get(f"{azure_url}/health", timeout=30)
        
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"✅ Health endpoint works")
            print(f"Version: {health_data.get('version', 'unknown')}")
            print(f"Message: {health_data.get('message', 'unknown')}")
            print(f"Deployment: {health_data.get('deployment', 'unknown')}")
            
            if health_data.get('version') == '1.0.2':
                print("✅ Latest version (1.0.2) is deployed!")
            else:
                print("⚠️ Old version detected!")
        else:
            print(f"❌ Health endpoint failed: {health_response.status_code}")
            
        # Test if new routes exist
        print("\n2. Testing if new routes are registered...")
        test_routes = ["/test-admin", "/adminlogin", "/admin/simple"]
        
        for route in test_routes:
            try:
                response = requests.get(f"{azure_url}{route}", timeout=10)
                if response.status_code == 200:
                    print(f"✅ {route} - Working!")
                elif response.status_code == 405:
                    print(f"❌ {route} - 405 Method Not Allowed")
                elif response.status_code == 404:
                    print(f"❌ {route} - 404 Not Found (route not registered)")
                else:
                    print(f"⚠️ {route} - Status {response.status_code}")
            except Exception as e:
                print(f"❌ {route} - Error: {e}")
                
    except Exception as e:
        print(f"❌ Error checking version: {e}")

if __name__ == "__main__":
    check_azure_version()