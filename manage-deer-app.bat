@echo off
echo ================================================
echo 🦌 DEER HUNTING APP MANAGEMENT 🦌
echo ================================================
echo.
echo Your Professional Deer Hunting App
echo Domain: https://app.deerpredictapp.org
echo.
echo [1] Check App Status
echo [2] Start Tunnel (if not running)
echo [3] Stop All Tunnels
echo [4] Test Domain Connection
echo [5] View Tunnel Info
echo [6] Exit
echo.
set /p choice="Enter your choice (1-6): "

if "%choice%"=="1" goto status
if "%choice%"=="2" goto start
if "%choice%"=="3" goto stop
if "%choice%"=="4" goto test
if "%choice%"=="5" goto info
if "%choice%"=="6" goto exit

:status
echo.
echo === CHECKING STATUS ===
echo.
echo Streamlit App Status:
netstat -ano | findstr :8501
echo.
echo Tunnel Status:
cloudflared tunnel info deer-hunting-app
pause
goto menu

:start
echo.
echo === STARTING TUNNEL ===
echo.
Start-Process -FilePath "cloudflared" -ArgumentList "tunnel","--config","cloudflare-config.yml","run" -WindowStyle Minimized
echo Tunnel started in background!
echo Wait 30 seconds then try: https://app.deerpredictapp.org
pause
goto menu

:stop
echo.
echo === STOPPING TUNNELS ===
echo.
taskkill /F /IM cloudflared.exe 2>nul
echo All tunnels stopped.
pause
goto menu

:test
echo.
echo === TESTING CONNECTION ===
echo.
powershell -Command "$headers = @{'Host' = 'app.deerpredictapp.org'}; try { $response = Invoke-WebRequest -Uri 'https://104.21.23.122' -Headers $headers -Method Head -TimeoutSec 15; Write-Host 'SUCCESS: Domain is working! Status:' $response.StatusCode } catch { Write-Host 'Error:' $_.Exception.Message }"
pause
goto menu

:info
echo.
echo === TUNNEL INFORMATION ===
echo.
cloudflared tunnel info deer-hunting-app
pause
goto menu

:menu
cls
echo ================================================
echo 🦌 DEER HUNTING APP MANAGEMENT 🦌
echo ================================================
echo.
echo Your Professional Deer Hunting App
echo Domain: https://app.deerpredictapp.org
echo.
echo [1] Check App Status
echo [2] Start Tunnel (if not running)
echo [3] Stop All Tunnels
echo [4] Test Domain Connection
echo [5] View Tunnel Info
echo [6] Exit
echo.
set /p choice="Enter your choice (1-6): "

if "%choice%"=="1" goto status
if "%choice%"=="2" goto start
if "%choice%"=="3" goto stop
if "%choice%"=="4" goto test
if "%choice%"=="5" goto info
if "%choice%"=="6" goto exit
goto menu

:exit
echo.
echo ================================================
echo 🦌 Professional Deer Hunting App Ready! 🦌
echo Domain: https://app.deerpredictapp.org
echo ================================================
pause
