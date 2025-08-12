#!/usr/bin/env python3
"""
Streamlit Frontend Launcher
Handles Streamlit configuration and startup automatically
"""

import os
import sys
import subprocess
from pathlib import Path

def setup_streamlit_config():
    """Create Streamlit config to disable email prompt"""
    config_dir = Path.home() / ".streamlit"
    config_dir.mkdir(exist_ok=True)
    
    config_file = config_dir / "config.toml"
    config_content = """[browser]
gatherUsageStats = false

[server]
headless = true
enableCORS = false
"""
    
    config_file.write_text(config_content)
    print(f"✅ Created Streamlit config at {config_file}")

def start_frontend():
    """Start the Streamlit frontend"""
    print("🚀 Starting Vermont Deer Prediction Frontend...")
    
    # Set working directory to frontend
    frontend_dir = Path(__file__).parent / "frontend"
    os.chdir(frontend_dir)
    
    # Setup config
    setup_streamlit_config()
    
    # Start Streamlit
    cmd = [sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", "8501"]
    
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"🔧 Command: {' '.join(cmd)}")
    print("🌐 Frontend will be available at: http://localhost:8501")
    print("⏳ Starting...")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n⏹️ Shutting down frontend...")
    except Exception as e:
        print(f"❌ Error starting frontend: {e}")

if __name__ == "__main__":
    start_frontend()
