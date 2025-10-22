#!/usr/bin/env python3
"""
Deployment verification script - checks if the app can be reached on Azure
"""

import urllib.request
import json
import time

AZURE_URL = "https://ownnoteapp-hedxcahwcrhwb8hb.canadacentral-01.azurewebsites.net"

def test_endpoint(url, description):
    """Test if an endpoint is reachable"""
    print(f"Testing {description}...", end=" ")
    
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (deployment test)')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            status = response.getcode()
            if status == 200:
                try:
                    data = json.loads(response.read().decode('utf-8'))
                    print(f"SUCCESS (200) - {data.get('message', 'OK')}")
                    return True
                except:
                    print(f"SUCCESS (200) - Response received")
                    return True
            else:
                print(f"RESPONSE ({status})")
                return status < 400
    except urllib.error.HTTPError as e:
        print(f"HTTP ERROR ({e.code})")
        return False
    except urllib.error.URLError as e:
        print(f"CONNECTION ERROR - {e.reason}")
        return False
    except Exception as e:
        print(f"ERROR - {e}")
        return False

def main():
    print("=" * 60)
    print("AZURE DEPLOYMENT VERIFICATION")
    print("=" * 60)
    print(f"Target URL: {AZURE_URL}")
    print()
    
    # Test endpoints
    endpoints = [
        ("/", "Root endpoint"),
        ("/health", "Health check"),
        ("/docs", "API Documentation"),
        ("/cors-debug", "CORS configuration"),
    ]
    
    results = []
    for endpoint, description in endpoints:
        url = AZURE_URL + endpoint
        success = test_endpoint(url, description)
        results.append((endpoint, success))
        time.sleep(1)  # Be nice to the server
    
    print()
    print("=" * 60)
    print("DEPLOYMENT STATUS SUMMARY")
    print("=" * 60)
    
    success_count = sum(1 for _, success in results if success)
    total_count = len(results)
    
    for endpoint, success in results:
        status = "PASS" if success else "FAIL"
        print(f"{endpoint:15} | {status}")
    
    print()
    if success_count == total_count:
        print("DEPLOYMENT STATUS: SUCCESS!")
        print("Your application is live and accessible.")
        print()
        print("Next steps:")
        print("1. Test your frontend integration")
        print("2. Verify CORS is working from GitHub Pages")
        print("3. Test user registration and notes functionality")
    elif success_count > 0:
        print("DEPLOYMENT STATUS: PARTIAL SUCCESS")
        print("Some endpoints are working. Check Azure logs for issues.")
    else:
        print("DEPLOYMENT STATUS: FAILED")
        print("Application is not accessible. Check Azure deployment logs.")
    
    print()
    print("Azure Portal: https://portal.azure.com")
    print("App Service: ownnoteapp-hedxcahwcrhwb8hb")

if __name__ == "__main__":
    main()