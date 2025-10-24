#!/usr/bin/env python3
"""
Monitor Azure deployment until it updates to the new version
"""

import requests
import time
import sys

def test_azure_admin():
    """Test if Azure admin login redirects properly"""
    azure_url = "https://ownnoteapp-hedxcahwcrhwb8hb.canadacentral-01.azurewebsites.net"
    
    try:
        login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        
        response = requests.post(
            f"{azure_url}/admin/login", 
            data=login_data,
            headers={"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"},
            allow_redirects=False,
            timeout=10
        )
        
        if response.status_code == 302:
            return True, "✅ NEW VERSION: Login redirects properly"
        elif response.status_code == 200:
            try:
                data = response.json()
                if 'access_token' in data:
                    return False, "❌ OLD VERSION: Still returning JSON"
            except:
                pass
            return True, "✅ LOGIN PAGE: Returning HTML"
        else:
            return False, f"❓ UNKNOWN: Status {response.status_code}"
            
    except Exception as e:
        return False, f"❌ ERROR: {e}"

def main():
    print("🔄 Monitoring Azure deployment update...")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    check_count = 0
    while True:
        check_count += 1
        print(f"\n[Check #{check_count}] {time.strftime('%H:%M:%S')}")
        
        is_updated, message = test_azure_admin()
        print(message)
        
        if is_updated and "NEW VERSION" in message:
            print("\n🎉 SUCCESS! Azure has been updated!")
            print("You can now use the admin dashboard at:")
            print("https://ownnoteapp-hedxcahwcrhwb8hb.canadacentral-01.azurewebsites.net/admin/login")
            break
        elif is_updated and "LOGIN PAGE" in message:
            print("✅ Azure is responding, login page loads correctly")
            break
        
        print("⏳ Waiting 30 seconds before next check...")
        try:
            time.sleep(30)
        except KeyboardInterrupt:
            print("\n\n👋 Monitoring stopped by user")
            sys.exit(0)

if __name__ == "__main__":
    main()