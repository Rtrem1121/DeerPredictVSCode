#!/usr/bin/env powershell
# Cloudflare Tunnel Status Check for Deer Prediction App

Write-Host "🔍 DEER PREDICTION APP - STATUS CHECK" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green
Write-Host ""

# Check Docker containers
Write-Host "📦 Docker Container Status:" -ForegroundColor Yellow
try {
    $containers = docker-compose ps
    Write-Host $containers
    
    # Check if all containers are up
    if ($containers -match "Up.*healthy" -and $containers -match "frontend" -and $containers -match "backend") {
        Write-Host "✅ All Docker containers are healthy" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Some containers may have issues" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Docker not available or containers not running" -ForegroundColor Red
}

Write-Host ""

# Check local services
Write-Host "🌐 Local Service Status:" -ForegroundColor Yellow
try {
    $frontendResponse = Invoke-WebRequest -Uri "http://localhost:8501/_stcore/health" -TimeoutSec 5 -UseBasicParsing
    if ($frontendResponse.StatusCode -eq 200) {
        Write-Host "✅ Frontend (port 8501): Healthy" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Frontend (port 8501): Not responding" -ForegroundColor Red
}

try {
    $backendResponse = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -UseBasicParsing
    if ($backendResponse.StatusCode -eq 200) {
        Write-Host "✅ Backend (port 8000): Healthy" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Backend (port 8000): Not responding" -ForegroundColor Red
}

Write-Host ""

# Check public URL
Write-Host "🌍 Public URL Status:" -ForegroundColor Yellow
try {
    $publicResponse = Invoke-WebRequest -Uri "https://app.deerpredictapp.org" -TimeoutSec 10 -UseBasicParsing
    if ($publicResponse.StatusCode -eq 200) {
        Write-Host "✅ Public URL: https://app.deerpredictapp.org - Accessible" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Public URL: Not accessible or tunnel down" -ForegroundColor Red
    Write-Host "   Try starting tunnel: .\start-cloudflare.ps1" -ForegroundColor Yellow
}

Write-Host ""

# Check tunnel process
Write-Host "🚇 Cloudflare Tunnel Status:" -ForegroundColor Yellow
$tunnelProcess = Get-Process -Name "cloudflared" -ErrorAction SilentlyContinue
if ($tunnelProcess) {
    Write-Host "✅ Tunnel process is running (PID: $($tunnelProcess.Id))" -ForegroundColor Green
} else {
    Write-Host "❌ Tunnel process not found" -ForegroundColor Red
    Write-Host "   Start tunnel: .\start-cloudflare.ps1" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📊 Quick Actions:" -ForegroundColor Cyan
Write-Host "   Start tunnel: .\start-cloudflare.ps1" -ForegroundColor White
Write-Host "   Restart containers: docker-compose restart" -ForegroundColor White
Write-Host "   View logs: docker-compose logs -f" -ForegroundColor White
Write-Host "   Check this status: .\check-status.ps1" -ForegroundColor White
