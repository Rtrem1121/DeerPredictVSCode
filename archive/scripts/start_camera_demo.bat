@echo off
echo =====================================
echo  Trail Camera Placement Demo Server
echo =====================================
echo.
echo Starting demo server on port 8001...
echo.
echo IMPORTANT: Make sure your main deer prediction app is running first!
echo Main app should be at: http://localhost:8000
echo.
echo Demo will be available at: http://localhost:8001
echo.
pause

python camera_demo_server.py
