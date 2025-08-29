#!/usr/bin/env powershell
# Cloudflare Tunnel Startup Script for Deer Prediction App
# Run this script to start the tunnel after starting your Docker containers

Write-Host "🚀 DEER PREDICTION APP - CLOUDFLARE TUNNEL STARTUP" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green
Write-Host ""

# Check if Docker containers are running
Write-Host "🔍 Checking Docker containers..." -ForegroundColor Yellow
$containers = docker-compose ps --services --filter "status=running"

if ($containers -match "frontend" -and $containers -match "backend") {
    Write-Host "✅ Docker containers are running" -ForegroundColor Green
} else {
    Write-Host "❌ Docker containers not running. Starting them first..." -ForegroundColor Red
    Write-Host "   Running: docker-compose up -d" -ForegroundColor Yellow
    docker-compose up -d
    Start-Sleep -Seconds 10
}

# Check if cloudflared is installed
Write-Host "🔍 Checking cloudflared installation..." -ForegroundColor Yellow
try {
    $version = cloudflared version
    Write-Host "✅ Cloudflared installed: $version" -ForegroundColor Green
} catch {
    Write-Host "❌ Cloudflared not installed. Please install it first:" -ForegroundColor Red
    Write-Host "   Download from: https://github.com/cloudflare/cloudflared/releases" -ForegroundColor Yellow
    exit 1
}

# Start the tunnel
Write-Host ""
Write-Host "🌐 Starting Cloudflare Tunnel..." -ForegroundColor Yellow
Write-Host "   URL: https://app.deerpredictapp.org" -ForegroundColor Cyan
Write-Host "   Local: http://localhost:8501" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Tunnel will run in foreground. Press Ctrl+C to stop." -ForegroundColor Yellow
Write-Host ""

# Run the tunnel
cloudflared tunnel --config cloudflare-config.yml run
