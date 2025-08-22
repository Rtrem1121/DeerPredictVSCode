#!/usr/bin/env python3
"""
Test Cloudflare Access Protection Status
Tests if the domain requires authentication
"""

import requests
import sys

def test_access_protection():
    """Test if Cloudflare Access is protecting the domain"""
    url = "https://app.deerpredictapp.org"
    
    try:
        print(f"Testing access protection for: {url}")
        response = requests.get(url, allow_redirects=False)
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        # Check for Cloudflare Access indicators
        if response.status_code == 302:
            location = response.headers.get('Location', '')
            if 'cloudflareaccess.com' in location:
                print("✅ PROTECTED: Cloudflare Access is active")
                return True
            else:
                print(f"⚠️  REDIRECT: Redirecting to {location}")
                return False
        elif response.status_code == 200:
            print("❌ NOT PROTECTED: Direct access allowed")
            return False
        else:
            print(f"⚠️  UNEXPECTED: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Error testing access: {e}")
        return False

if __name__ == "__main__":
    is_protected = test_access_protection()
    sys.exit(0 if is_protected else 1)
