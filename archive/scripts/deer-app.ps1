#!/usr/bin/env powershell
# Unified Deer Prediction App Startup Script
# Manages both Docker containers and Cloudflare tunnel

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("start", "stop", "restart", "status", "logs")]
    [string]$Action = "start"
)

$ErrorActionPreference = "Stop"

Write-Host "🦌 Deer Prediction App Manager" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green

function Start-DeerApp {
    Write-Host "🚀 Starting Deer Prediction App..." -ForegroundColor Blue
    
    # Step 1: Start Docker containers
    Write-Host "[1/3] Starting Docker containers..." -ForegroundColor Yellow
    docker-compose up -d
    
    # Step 2: Wait for containers to be healthy
    Write-Host "[2/3] Waiting for containers to be healthy..." -ForegroundColor Yellow
    $maxWait = 60
    $waited = 0
    do {
        $backendHealthy = (docker-compose ps backend | Select-String "healthy") -ne $null
        $frontendHealthy = (docker-compose ps frontend | Select-String "healthy") -ne $null
        
        if ($backendHealthy -and $frontendHealthy) {
            Write-Host "✅ All containers are healthy!" -ForegroundColor Green
            break
        }
        
        Start-Sleep -Seconds 5
        $waited += 5
        Write-Host "   Waiting... ($waited/$maxWait seconds)" -ForegroundColor DarkYellow
    } while ($waited -lt $maxWait)
    
    if ($waited -ge $maxWait) {
        Write-Host "❌ Containers failed to become healthy in time" -ForegroundColor Red
        return $false
    }
    
    # Step 3: Start Cloudflare tunnel
    Write-Host "[3/3] Starting Cloudflare tunnel..." -ForegroundColor Yellow
    $tunnel = Start-Process -WindowStyle Hidden -FilePath "cloudflared" -ArgumentList "tunnel", "run", "deer-hunting-app" -PassThru
    
    Start-Sleep -Seconds 10
    
    if ($tunnel.HasExited) {
        Write-Host "❌ Cloudflare tunnel failed to start" -ForegroundColor Red
        return $false
    }
    
    Write-Host "🎉 Deer Prediction App is running!" -ForegroundColor Green
    Write-Host "📱 Public URL: https://app.deerpredictapp.org" -ForegroundColor Cyan
    Write-Host "🔧 Local Frontend: http://localhost:8501" -ForegroundColor Cyan
    Write-Host "🔧 Local API: http://localhost:8000/docs" -ForegroundColor Cyan
    
    return $true
}

function Stop-DeerApp {
    Write-Host "🛑 Stopping Deer Prediction App..." -ForegroundColor Red
    
    # Stop Cloudflare tunnel
    Write-Host "[1/2] Stopping Cloudflare tunnel..." -ForegroundColor Yellow
    Get-Process cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force
    
    # Stop Docker containers
    Write-Host "[2/2] Stopping Docker containers..." -ForegroundColor Yellow
    docker-compose down
    
    Write-Host "✅ Deer Prediction App stopped successfully!" -ForegroundColor Green
}

function Show-Status {
    Write-Host "📊 System Status:" -ForegroundColor Blue
    Write-Host "=================" -ForegroundColor Blue
    
    # Docker status
    Write-Host "`n🐳 Docker Containers:" -ForegroundColor Cyan
    docker-compose ps
    
    # Cloudflare tunnel status
    Write-Host "`n☁️ Cloudflare Tunnel:" -ForegroundColor Cyan
    $tunnelProcess = Get-Process cloudflared -ErrorAction SilentlyContinue
    if ($tunnelProcess) {
        Write-Host "Status: Running (PID: $($tunnelProcess.Id))" -ForegroundColor Green
    } else {
        Write-Host "Status: Not running" -ForegroundColor Red
    }
    
    # Test connectivity
    Write-Host "`n🌐 Connectivity Test:" -ForegroundColor Cyan
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8501" -Method Head -TimeoutSec 5
        Write-Host "Local Frontend: ✅ Accessible" -ForegroundColor Green
    } catch {
        Write-Host "Local Frontend: ❌ Not accessible" -ForegroundColor Red
    }
    
    try {
        $response = Invoke-WebRequest -Uri "https://app.deerpredictapp.org" -Method Head -TimeoutSec 10
        Write-Host "Public URL: ✅ Accessible" -ForegroundColor Green
    } catch {
        Write-Host "Public URL: ❌ Not accessible" -ForegroundColor Red
    }
}

function Show-Logs {
    Write-Host "📄 Application Logs:" -ForegroundColor Blue
    docker-compose logs -f --tail=50
}

# Main execution
switch ($Action) {
    "start" { 
        if (Start-DeerApp) {
            Write-Host "`n💡 Tip: Use '.\deer-app.ps1 status' to check system health" -ForegroundColor DarkCyan
        }
    }
    "stop" { Stop-DeerApp }
    "restart" { 
        Stop-DeerApp
        Start-Sleep -Seconds 5
        Start-DeerApp
    }
    "status" { Show-Status }
    "logs" { Show-Logs }
    default {
        Write-Host "Usage: .\deer-app.ps1 {start|stop|restart|status|logs}" -ForegroundColor Yellow
        Write-Host "  start   - Start the complete deer prediction app" -ForegroundColor White
        Write-Host "  stop    - Stop all services" -ForegroundColor White
        Write-Host "  restart - Restart all services" -ForegroundColor White
        Write-Host "  status  - Show system status and connectivity" -ForegroundColor White
        Write-Host "  logs    - Show application logs" -ForegroundColor White
    }
}
