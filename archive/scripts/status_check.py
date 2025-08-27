#!/usr/bin/env python3
"""
Quick Status Check for Deer Hunting App
Verifies all services are running correctly
"""

import subprocess
import requests
import sys

def check_streamlit():
    """Check if Streamlit is running"""
    try:
        result = subprocess.run(['tasklist', '/fi', 'imagename eq streamlit.exe'], 
                              capture_output=True, text=True)
        if 'streamlit.exe' in result.stdout:
            print("✅ Streamlit: Running")
            return True
        else:
            print("❌ Streamlit: Not running")
            return False
    except Exception as e:
        print(f"⚠️  Streamlit check error: {e}")
        return False

def check_cloudflare():
    """Check if Cloudflare tunnel is running"""
    try:
        result = subprocess.run(['tasklist', '/fi', 'imagename eq cloudflared.exe'], 
                              capture_output=True, text=True)
        if 'cloudflared.exe' in result.stdout:
            print("✅ Cloudflare Tunnel: Running")
            return True
        else:
            print("❌ Cloudflare Tunnel: Not running")
            return False
    except Exception as e:
        print(f"⚠️  Cloudflare check error: {e}")
        return False

def check_domain():
    """Check if domain is accessible"""
    try:
        response = requests.get("https://app.deerpredictapp.org", timeout=10)
        if response.status_code == 200:
            print("✅ Domain: Accessible")
            return True
        else:
            print(f"⚠️  Domain: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Domain: Not accessible - {e}")
        return False

def main():
    print("🦌 DEER HUNTING APP STATUS CHECK")
    print("="*40)
    
    streamlit_ok = check_streamlit()
    cloudflare_ok = check_cloudflare()
    domain_ok = check_domain()
    
    print("\n📊 SUMMARY:")
    if streamlit_ok and cloudflare_ok and domain_ok:
        print("✅ ALL SYSTEMS OPERATIONAL")
        print("🌐 App ready at: https://app.deerpredictapp.org")
        print("🔐 Password: DeerHunter2025!")
    else:
        print("⚠️  ISSUES DETECTED")
        if not streamlit_ok:
            print("   → Run: streamlit run frontend/app.py --server.port 8501")
        if not cloudflare_ok:
            print("   → Run: cloudflared tunnel --config cloudflare-config.yml run")
        if not domain_ok:
            print("   → Check tunnel and DNS settings")
    
    return streamlit_ok and cloudflare_ok and domain_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
