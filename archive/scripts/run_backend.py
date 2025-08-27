#!/usr/bin/env python3
"""
Stable Backend Server Runner
Ensures the backend stays running and handles errors gracefully
"""

import sys
import os
import time
import subprocess
from pathlib import Path

def run_backend_server():
    """Run the backend server with proper error handling"""
    
    # Set working directory
    app_dir = Path(__file__).parent
    os.chdir(app_dir)
    
    # Set Python path
    os.environ['PYTHONPATH'] = str(app_dir)
    
    print("🚀 Starting Deer Prediction Backend Server...")
    print(f"📁 Working directory: {app_dir}")
    print(f"🐍 Python path: {os.environ['PYTHONPATH']}")
    
    try:
        # Start uvicorn server
        cmd = [
            sys.executable, "-m", "uvicorn", "backend.main:app",
            "--host", "127.0.0.1",
            "--port", "8000",
            "--no-access-log",
            "--no-server-header"
        ]
        
        print(f"⚡ Executing: {' '.join(cmd)}")
        
        # Run the server
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        print("✅ Backend server started successfully!")
        print("🌐 Server running on http://127.0.0.1:8000")
        print("🎯 Endpoints available:")
        print("   - POST /predict - Hunting predictions")
        print("   - GET /scouting/types - Observation types")
        print("   - GET /scouting/observations - Scouting data")
        print("   - POST /trail-cameras - Camera placement")
        print("\n" + "="*50)
        print("📊 Server Output:")
        print("="*50)
        
        # Stream output
        for line in iter(process.stdout.readline, ''):
            if line:
                print(line.rstrip())
                
        # Wait for process to complete
        process.wait()
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        if process:
            process.terminate()
    except Exception as e:
        print(f"❌ Error running server: {e}")
        return False
        
    return True

if __name__ == "__main__":
    run_backend_server()
