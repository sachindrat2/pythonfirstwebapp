#!/usr/bin/env python3
"""
Script to check Azure deployment status and force update if needed
"""

import requests
import time

def check_azure_status():
    """Check if Azure has updated to the new Docker image"""
    azure_url = "https://ownnoteapp-hedxcahwcrhwb8hb.canadacentral-01.azurewebsites.net"
    
    print("🔍 Checking Azure deployment status...")
    print("=" * 50)
    
    # Check version endpoint
    try:
        response = requests.get(f"{azure_url}/health", timeout=10)
        print(f"Health check: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Version: {data.get('version', 'Unknown')}")
            print(f"Status: {data.get('status', 'Unknown')}")
        else:
            print(f"Health check failed: {response.status_code}")
    except Exception as e:
        print(f"Health check error: {e}")
    
    # Test admin login behavior
    print("\n🧪 Testing admin login behavior...")
    try:
        login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        
        # Test with HTML accept header (should redirect)
        response = requests.post(
            f"{azure_url}/admin/login", 
            data=login_data,
            headers={"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"},
            allow_redirects=False
        )
        
        print(f"Login response status: {response.status_code}")
        
        if response.status_code == 302:
            print("✅ NEW VERSION DETECTED: Login returns redirect (302)")
            location = response.headers.get('Location', 'No location header')
            print(f"Redirect location: {location}")
        elif response.status_code == 200:
            try:
                data = response.json()
                if 'access_token' in data:
                    print("❌ OLD VERSION: Login returns JSON instead of redirect")
                    print("Azure is still using the old Docker image")
                else:
                    print("✅ LOGIN PAGE: Returns HTML login page")
            except:
                print("✅ LOGIN PAGE: Returns HTML content")
        else:
            print(f"Unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"Login test error: {e}")

def main():
    print("🚀 Azure Deployment Update Checker")
    print("=" * 50)
    
    check_azure_status()
    
    print("\n📋 Next Steps:")
    print("1. If showing OLD VERSION:")
    print("   - Wait 5-10 minutes for Azure to auto-update")
    print("   - Or manually restart the Azure App Service")
    print("   - Or trigger a new deployment")
    print("\n2. If showing NEW VERSION:")
    print("   - Try accessing the admin dashboard")
    print("   - Login should work with proper redirection")
    
    print(f"\n🔗 Test URL: https://ownnoteapp-hedxcahwcrhwb8hb.canadacentral-01.azurewebsites.net/admin/login")

if __name__ == "__main__":
    main()