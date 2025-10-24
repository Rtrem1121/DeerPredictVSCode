"""Start Docker services"""
import subprocess
import time

print("Starting Docker services...")
print("="*60)

# Check if Docker Desktop is running
print("\n1. Checking if Docker Desktop is running...")
result = subprocess.run(["docker", "info"], capture_output=True)
if result.returncode != 0:
    print("   ❌ Docker Desktop is not running")
    print("   Please start Docker Desktop manually and wait for it to initialize")
    print("   Then run: docker-compose -f docker/docker-compose.yml up --build")
    exit(1)

print("   ✅ Docker is running")

# Start services
print("\n2. Starting docker-compose services...")
print("   This will build and start backend + frontend containers")
print("   Press Ctrl+C to stop when done testing\n")

subprocess.run([
    "docker-compose", "-f", "docker/docker-compose.yml", "up", "--build"
], cwd=r"c:\Users\Rich\deer_pred_app")
