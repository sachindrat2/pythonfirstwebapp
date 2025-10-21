#!/usr/bin/env python3
"""
Deployment verification script for CORS fixes.
"""

import json
import urllib.request
import urllib.error

def test_cors_endpoints():
    """Test CORS-related endpoints on the deployed server."""
    base_url = "https://ownnoteapp-hedxcahwcrhwb8hb.canadacentral-01.azurewebsites.net"
    
    print("Testing CORS endpoints on deployed server...")
    
    # Test health endpoint
    try:
        response = urllib.request.urlopen(f"{base_url}/health")
        data = json.loads(response.read().decode('utf-8'))
        print(f"✅ Health check: {data['status']}")
        print(f"   CORS origins configured: {data['cors_origins']}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    
    # Test CORS test endpoint
    try:
        req = urllib.request.Request(f"{base_url}/cors-test")
        req.add_header('Origin', 'https://sachindrat2.github.io')
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode('utf-8'))
        print(f"✅ CORS test: {data['message']}")
        print(f"   Origin detected: {data.get('origin', 'None')}")
    except Exception as e:
        print(f"❌ CORS test failed: {e}")
    
    # Test OPTIONS preflight
    try:
        req = urllib.request.Request(f"{base_url}/notes", method='OPTIONS')
        req.add_header('Origin', 'https://sachindrat2.github.io')
        req.add_header('Access-Control-Request-Method', 'POST')
        req.add_header('Access-Control-Request-Headers', 'Authorization, Content-Type')
        response = urllib.request.urlopen(req)
        print("✅ OPTIONS preflight request successful")
        
        # Check CORS headers
        headers = dict(response.headers)
        if 'Access-Control-Allow-Origin' in headers:
            print(f"   Access-Control-Allow-Origin: {headers['Access-Control-Allow-Origin']}")
        else:
            print("   ❌ Access-Control-Allow-Origin header missing")
            
    except Exception as e:
        print(f"❌ OPTIONS preflight failed: {e}")

if __name__ == "__main__":
    test_cors_endpoints()