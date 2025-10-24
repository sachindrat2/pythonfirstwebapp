#!/usr/bin/env python3
"""
Test script to check Azure deployment status
"""
import requests
import time

def test_azure_deployment():
    """Test if the Azure app is responding"""
    azure_url = "https://ownnoteapp.azurewebsites.net"
    
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
        
        # Test admin login
        print("\n3. Testing admin login page...")
        admin_response = requests.get(f"{azure_url}/admin/login", timeout=30)
        print(f"Admin Login Status: {admin_response.status_code}")
        
        if admin_response.status_code == 200:
            print("✅ Admin login page is accessible!")
        else:
            print(f"⚠️ Admin login returned status {admin_response.status_code}")
            
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