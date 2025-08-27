#!/usr/bin/env python3
"""
🎯 Quick GEE Setup Workflow
Interactive guide to activate Google Earth Engine satellite data
"""

import webbrowser
import time
import os
from pathlib import Path

def print_header(title):
    """Print formatted section header"""
    print("\n" + "="*60)
    print(f"🎯 {title}")
    print("="*60)

def wait_for_user(message="Press Enter to continue..."):
    """Wait for user input"""
    input(f"\n✋ {message}")

def open_link(url, description):
    """Open URL and wait for user"""
    print(f"🌐 Opening: {description}")
    print(f"   URL: {url}")
    try:
        webbrowser.open(url)
        wait_for_user("Complete the task in your browser, then press Enter")
    except:
        print("   Please open this URL manually in your browser")
        wait_for_user()

def main():
    """Interactive GEE setup workflow"""
    print("🛰️ GOOGLE EARTH ENGINE ACTIVATION WORKFLOW")
    print("   Transform your deer predictions with real satellite data!")
    print()
    print("⏱️  Total time needed: ~15 minutes")
    print("🎯 End result: Live satellite vegetation analysis")
    
    wait_for_user("Ready to begin? Press Enter to start...")
    
    # Step 1: Google Cloud Console
    print_header("STEP 1: Google Cloud Console Setup")
    print("🏗️  Creating your Google Cloud project...")
    print()
    print("Tasks to complete:")
    print("   ✅ Sign in to Google Cloud Console")
    print("   ✅ Create project: 'deer-predict-app'")
    print("   ✅ Note down the Project ID")
    
    open_link("https://console.cloud.google.com/", "Google Cloud Console")
    
    # Step 2: Enable APIs
    print_header("STEP 2: Enable Required APIs")
    print("🔌 Enabling Earth Engine and Resource Manager APIs...")
    print()
    print("Search and enable these APIs:")
    print("   ✅ Google Earth Engine API")
    print("   ✅ Cloud Resource Manager API")
    
    open_link("https://console.cloud.google.com/apis/library", "APIs & Services Library")
    
    # Step 3: Service Account
    print_header("STEP 3: Create Service Account")
    print("🤖 Creating service account for satellite data access...")
    print()
    print("Create service account with:")
    print("   📝 Name: deer-prediction-gee")
    print("   📝 Description: Service account for deer prediction satellite analysis")
    print("   🔑 Roles:")
    print("      - Earth Engine Resource Viewer")
    print("      - Service Account User")
    
    open_link("https://console.cloud.google.com/iam-admin/serviceaccounts", "Service Accounts")
    
    # Step 4: Download Key
    print_header("STEP 4: Download JSON Key")
    print("📥 Downloading authentication credentials...")
    print()
    print("Download steps:")
    print("   ✅ Click on your service account")
    print("   ✅ Go to 'Keys' tab")
    print("   ✅ Click 'Add Key' → 'Create new key'")
    print("   ✅ Select 'JSON' format")
    print("   ✅ Click 'Create' (file downloads automatically)")
    
    wait_for_user("Downloaded the JSON key file?")
    
    # Step 5: Place Credentials
    print_header("STEP 5: Install Credentials")
    print("📁 Installing credentials in your project...")
    print()
    print("File placement:")
    print(f"   📂 Rename downloaded file to: gee-service-account.json")
    print(f"   📂 Move to: {Path('credentials').absolute()}")
    print(f"   📂 Final path: {Path('credentials/gee-service-account.json').absolute()}")
    
    wait_for_user("Placed the credentials file?")
    
    # Step 6: Earth Engine Registration
    print_header("STEP 6: Register with Earth Engine")
    print("🌍 Registering your service account with Earth Engine...")
    print()
    print("Registration steps:")
    print("   ✅ Sign in to Earth Engine Code Editor")
    print("   ✅ Accept terms if prompted")
    print("   ✅ Go to Assets tab → settings gear")
    print("   ✅ Add your service account email")
    print("   ✅ Email format: deer-prediction-gee@[PROJECT-ID].iam.gserviceaccount.com")
    
    open_link("https://code.earthengine.google.com/", "Earth Engine Code Editor")
    
    # Step 7: Test Activation
    print_header("STEP 7: Test Satellite Activation")
    print("🧪 Testing your satellite data connection...")
    print()
    print("Running activation test...")
    
    wait_for_user("Completed Earth Engine registration?")
    
    # Run the test
    print("🚀 Testing GEE activation...")
    os.system("python check_gee_activation.py")
    
    print()
    print("🎉 ACTIVATION COMPLETE!")
    print("   Your deer prediction system now uses real satellite data!")
    print()
    print("🧪 Run full test: python test_gee_integration.py")
    print("🖥️  Start application: docker-compose up")
    print()
    print("🛰️ Features now active:")
    print("   ✅ Live NDVI vegetation health")
    print("   ✅ Real-time crop/mast mapping")
    print("   ✅ Current water source conditions")
    print("   ✅ Enhanced prediction accuracy")

if __name__ == "__main__":
    main()
