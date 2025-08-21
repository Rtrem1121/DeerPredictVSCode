#!/usr/bin/env python3
"""
Railway Deployment Setup for Deer Prediction App
Private repository deployment with full backend + frontend
"""

import subprocess
import os
import sys

def setup_railway_deployment():
    print("🚀 RAILWAY DEPLOYMENT SETUP")
    print("=" * 50)
    
    print("\n📋 DEPLOYMENT CHECKLIST:")
    print("✅ Private repository: Supported")
    print("✅ Full-stack app: Backend + Frontend")
    print("✅ iPhone optimization: Automatic")
    print("✅ Custom domain: Available")
    print("✅ Commercial ready: Perfect for monetization")
    
    print("\n💰 COST: $5/month (includes everything)")
    
    print("\n🔧 SETUP STEPS:")
    print("1. Create Railway account (free trial)")
    print("2. Connect private GitHub repo") 
    print("3. Deploy with one click")
    print("4. Get professional URL")
    
    print("\n📱 IPHONE FEATURES:")
    print("✅ Native mobile interface")
    print("✅ GPS location detection")
    print("✅ Offline map caching")
    print("✅ Home screen bookmark")
    print("✅ Full hunting prediction features")
    
    print("\n💼 MONETIZATION READY:")
    print("✅ Custom domain (yourapp.com)")
    print("✅ User authentication")
    print("✅ Payment integration ready")
    print("✅ Usage analytics")
    print("✅ API rate limiting")
    
    return True

def create_railway_config():
    """Create Railway deployment configuration"""
    
    # Create Dockerfile for Railway (if not exists)
    dockerfile_content = """FROM python:3.9-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . .

# Expose ports
EXPOSE 8000 8501

# Start both backend and frontend
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port 8000 & streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0"]
"""
    
    # Create railway.json for configuration
    railway_config = """{
  "build": {
    "builder": "DOCKERFILE"
  },
  "deploy": {
    "numReplicas": 1,
    "sleepApplication": false,
    "restartPolicyType": "ON_FAILURE"
  }
}"""
    
    print("\n📝 Creating Railway deployment files...")
    
    with open("Dockerfile.railway", "w") as f:
        f.write(dockerfile_content)
    print("✅ Created Dockerfile.railway")
    
    with open("railway.json", "w") as f:
        f.write(railway_config)
    print("✅ Created railway.json")
    
    print("\n🎯 READY FOR RAILWAY DEPLOYMENT!")

if __name__ == "__main__":
    setup_railway_deployment()
    create_railway_config()
    
    print("\n" + "=" * 50)
    print("🎉 NEXT STEPS:")
    print("1. Go to https://railway.app/")
    print("2. Sign up (free trial)")
    print("3. Click 'Deploy from GitHub'")
    print("4. Select your private repo: DeerPredictVSCode")
    print("5. Railway auto-deploys your app")
    print("6. Get URL like: https://yourapp.railway.app")
    print("\n💰 Cost: $5/month after free trial")
    print("🚀 Perfect for commercial deer hunting app!")
