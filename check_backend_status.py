
import requests
import sys

BACKEND_URL = "http://localhost:8000"

def check_backend():
    print(f"🔍 Checking Backend Status at {BACKEND_URL}...")
    try:
        # Try root endpoint or health check
        response = requests.get(f"{BACKEND_URL}/", timeout=5)
        print(f"✅ Backend is reachable. Status Code: {response.status_code}")
        print(f"   Response: {response.text[:100]}...")
    except requests.exceptions.ConnectionError:
        print("❌ Connection Refused: Backend is NOT running or not reachable.")
        print("   Please ensure the backend server is started.")
    except requests.exceptions.Timeout:
        print("❌ Connection Timed Out: Backend is running but slow/unresponsive.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_backend()
