@echo off
echo ====================================
echo 🦌 DEER HUNTING APP - FULL STARTUP
echo ====================================

echo [1/3] Starting Backend API Server...
start "Backend API" cmd /k "cd /d %~dp0 && set PYTHONPATH=%~dp0 && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"

echo [2/3] Waiting for backend to initialize...
timeout /t 5 /nobreak >nul

echo [3/3] Starting Streamlit Frontend...
start "Frontend App" cmd /k "cd /d %~dp0 && streamlit run frontend/app.py --server.port 8501"

echo [4/4] Starting Cloudflare Tunnel...
start "Cloudflare Tunnel" cmd /k "cd /d %~dp0 && cloudflared tunnel --config cloudflare-config.yml run"

echo.
echo ✅ ALL SERVICES STARTING...
echo.
echo 🌐 App will be available at: https://app.deerpredictapp.org
echo 🔐 Password: DeerHunter2025!
echo 📊 API Docs: http://localhost:8000/docs
echo.
echo Services are starting in separate windows...
pause
