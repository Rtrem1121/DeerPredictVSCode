#!/usr/bin/env python3
"""
Development utilities for the Deer Prediction App
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_tests():
    """Run the test suite"""
    print("🧪 Running tests...")
    result = subprocess.run([sys.executable, "-m", "pytest", "-v"], cwd=Path(__file__).parent)
    return result.returncode == 0

def run_linting():
    """Run code linting"""
    print("🔍 Running linting...")
    # Check if flake8 is available
    try:
        result = subprocess.run([sys.executable, "-m", "flake8", "backend/", "frontend/"], 
                              cwd=Path(__file__).parent, capture_output=True)
        if result.returncode == 0:
            print("✅ Linting passed")
        else:
            print("❌ Linting failed:")
            print(result.stdout.decode())
            print(result.stderr.decode())
        return result.returncode == 0
    except FileNotFoundError:
        print("⚠️  flake8 not found, install with: pip install flake8")
        return False

def format_code():
    """Format code using black"""
    print("🎨 Formatting code...")
    try:
        subprocess.run([sys.executable, "-m", "black", "backend/", "frontend/"], 
                      cwd=Path(__file__).parent)
        print("✅ Code formatted")
        return True
    except FileNotFoundError:
        print("⚠️  black not found, install with: pip install black")
        return False

def check_env():
    """Check environment setup"""
    print("🔧 Checking environment...")
    
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        print("❌ .env file not found. Copy .env.example to .env and configure.")
        return False
    
    # Check for required environment variables
    required_vars = ["OPENWEATHERMAP_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ Environment setup looks good")
    return True

def build_docker():
    """Build Docker containers"""
    print("🐳 Building Docker containers...")
    result = subprocess.run(["docker-compose", "build"], cwd=Path(__file__).parent)
    return result.returncode == 0

def start_dev():
    """Start development servers"""
    print("🚀 Starting development servers...")
    result = subprocess.run(["docker-compose", "up"], cwd=Path(__file__).parent)
    return result.returncode == 0

def main():
    parser = argparse.ArgumentParser(description="Development utilities for Deer Prediction App")
    parser.add_argument("command", choices=[
        "test", "lint", "format", "check-env", "build", "start", "all"
    ], help="Command to run")
    
    args = parser.parse_args()
    
    if args.command == "test":
        return run_tests()
    elif args.command == "lint":
        return run_linting()
    elif args.command == "format":
        return format_code()
    elif args.command == "check-env":
        return check_env()
    elif args.command == "build":
        return build_docker()
    elif args.command == "start":
        return start_dev()
    elif args.command == "all":
        success = True
        success &= check_env()
        success &= format_code()
        success &= run_linting()
        success &= run_tests()
        if success:
            print("🎉 All checks passed!")
        else:
            print("❌ Some checks failed")
        return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
