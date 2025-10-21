#!/usr/bin/env python3
"""
Test the local CORS configuration.
"""

import json
import urllib.request
import urllib.error

def test_local_cors():
    """Test CORS configuration on local server."""
    base_url = "http://localhost:8000"
    
    print("Testing local CORS configuration...")
    
    # Test health endpoint
    try:
        response = urllib.request.urlopen(f"{base_url}/health")
        data = json.loads(response.read().decode('utf-8'))
        print(f"✅ Health check: {data['status']}")
        print(f"   CORS origins configured: {data['cors_origins']}")
        print(f"   Timestamp: {data['timestamp']}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    
    # Test CORS test endpoint with GitHub Pages origin
    try:
        req = urllib.request.Request(f"{base_url}/cors-test")
        req.add_header('Origin', 'https://sachindrat2.github.io')
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode('utf-8'))
        print(f"✅ CORS test: {data['message']}")
        print(f"   Origin detected: {data.get('origin', 'None')}")
        print(f"   GitHub Pages in allowed origins: {'https://sachindrat2.github.io' in data['allowed_origins']}")
    except Exception as e:
        print(f"❌ CORS test failed: {e}")
    
    # Test basic endpoints
    try:
        response = urllib.request.urlopen(f"{base_url}/test-visibility")
        data = json.loads(response.read().decode('utf-8'))
        print(f"✅ Test visibility: {data['status']}")
    except Exception as e:
        print(f"❌ Test visibility failed: {e}")

if __name__ == "__main__":
    test_local_cors()