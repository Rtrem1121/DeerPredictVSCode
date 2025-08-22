@echo off
title Stopping Deer Hunting App
color 0C
echo ================================================
echo 🦌 STOPPING DEER HUNTING APP 🦌
echo ================================================

echo Stopping Streamlit processes...
taskkill /IM "streamlit.exe" /F 2>nul
taskkill /IM "python.exe" /F 2>nul
if %errorlevel%==0 (
    echo ✅ Streamlit app stopped
) else (
    echo ℹ️ No Streamlit processes found
)

echo.
echo Stopping Cloudflare tunnel...
taskkill /IM "cloudflared.exe" /F 2>nul
if %errorlevel%==0 (
    echo ✅ Cloudflare tunnel stopped
) else (
    echo ℹ️ No tunnel processes found
)

echo.
echo ================================================
echo 🦌 DEER HUNTING APP OFFLINE 🦌
echo ================================================
echo.
echo ✅ All processes stopped
echo 🔒 Your hunting data is secure and private
echo 💰 $0 hosting costs while offline
echo.
echo Ready for your next hunting adventure!
echo.
pause
