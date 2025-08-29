@echo off
REM Cloudflare Tunnel Startup Script for Windows (Batch version)
REM Alternative to PowerShell script for environments where PS execution is restricted

echo.
echo 🚀 DEER PREDICTION APP - CLOUDFLARE TUNNEL STARTUP
echo ==================================================
echo.

echo 🔍 Checking Docker containers...
docker-compose ps | findstr "Up" >nul
if %errorlevel% neq 0 (
    echo ❌ Starting Docker containers first...
    docker-compose up -d
    timeout /t 10 /nobreak >nul
)

echo ✅ Docker containers ready
echo.

echo 🌐 Starting Cloudflare Tunnel...
echo    URL: https://app.deerpredictapp.org
echo    Local: http://localhost:8501
echo.
echo 📋 Press Ctrl+C to stop the tunnel
echo.

cloudflared tunnel --config cloudflare-config.yml run
