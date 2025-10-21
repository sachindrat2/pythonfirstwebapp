#!/usr/bin/env python3
"""
Test script to verify CORS configuration is working properly.
"""

import urllib.request
import urllib.error
import json

BASE_URL = "http://localhost:8000"
GITHUB_ORIGIN = "https://sachindrat2.github.io"

def test_cors_preflight(url, origin):
    """Test CORS preflight request"""
    print(f"\n🔍 Testing CORS preflight for {url}")
    
    req = urllib.request.Request(url, method="OPTIONS")
    req.add_header("Origin", origin)
    req.add_header("Access-Control-Request-Method", "POST")
    req.add_header("Access-Control-Request-Headers", "Content-Type,Authorization")
    
    try:
        with urllib.request.urlopen(req) as response:
            print(f"✅ Status: {response.status}")
            cors_headers = {
                k: v for k, v in response.headers.items() 
                if k.lower().startswith('access-control')
            }
            print("CORS Headers:")
            for header, value in cors_headers.items():
                print(f"  {header}: {value}")
            return True
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error: {e.code} - {e.reason}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_cors_actual_request(url, origin):
    """Test actual CORS request"""
    print(f"\n🔍 Testing actual CORS request for {url}")
    
    req = urllib.request.Request(url)
    req.add_header("Origin", origin)
    
    try:
        with urllib.request.urlopen(req) as response:
            print(f"✅ Status: {response.status}")
            data = json.loads(response.read().decode('utf-8'))
            print(f"Response: {json.dumps(data, indent=2)}")
            
            cors_headers = {
                k: v for k, v in response.headers.items() 
                if k.lower().startswith('access-control')
            }
            if cors_headers:
                print("CORS Headers in Response:")
                for header, value in cors_headers.items():
                    print(f"  {header}: {value}")
            return True
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error: {e.code} - {e.reason}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🧪 CORS Configuration Test")
    print("=" * 50)
    
    # Test endpoints to check
    endpoints = [
        "/health",
        "/cors-debug", 
        "/token",
        "/notes"
    ]
    
    origin = GITHUB_ORIGIN
    print(f"Testing with Origin: {origin}")
    
    results = []
    
    for endpoint in endpoints:
        url = BASE_URL + endpoint
        
        # Test preflight
        preflight_ok = test_cors_preflight(url, origin)
        
        # Test actual request (for GET endpoints)
        if endpoint in ["/health", "/cors-debug"]:
            actual_ok = test_cors_actual_request(url, origin)
        else:
            actual_ok = None  # Skip actual request for POST endpoints
        
        results.append({
            "endpoint": endpoint,
            "preflight": preflight_ok,
            "actual": actual_ok
        })
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 50)
    for result in results:
        endpoint = result["endpoint"]
        preflight = "✅" if result["preflight"] else "❌"
        actual = "✅" if result["actual"] else ("⏭️ " if result["actual"] is None else "❌")
        print(f"{endpoint:12} | Preflight: {preflight} | Actual: {actual}")
    
    # Overall result
    all_preflight_ok = all(r["preflight"] for r in results)
    print(f"\n🎯 Overall CORS Status: {'✅ WORKING' if all_preflight_ok else '❌ ISSUES FOUND'}")
    
    if all_preflight_ok:
        print("\n✅ CORS configuration looks good!")
        print("Next steps:")
        print("1. Deploy to Azure")  
        print("2. Test with your frontend")
    else:
        print("\n❌ CORS issues detected!")
        print("Check the server logs and configuration.")

if __name__ == "__main__":
    main()