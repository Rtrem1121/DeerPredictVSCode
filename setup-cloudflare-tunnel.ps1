# 🛠️ Cloudflare Tunnel Quick Setup Script
# Run this after installing cloudflared

Write-Host "================================================" -ForegroundColor Green
Write-Host "🦌 DEER HUNTING APP - CLOUDFLARE SETUP 🦌" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""

# Step 1: Check if cloudflared is installed
Write-Host "[1/5] Checking cloudflared installation..." -ForegroundColor Yellow
try {
    $version = cloudflared --version
    Write-Host "✅ cloudflared found: $version" -ForegroundColor Green
} catch {
    Write-Host "❌ cloudflared not found!" -ForegroundColor Red
    Write-Host "Please install from: https://github.com/cloudflare/cloudflared/releases" -ForegroundColor Red
    exit 1
}

# Step 2: Login to Cloudflare (if not already logged in)
Write-Host ""
Write-Host "[2/5] Cloudflare authentication..." -ForegroundColor Yellow
Write-Host "This will open your browser to login to Cloudflare..." -ForegroundColor Cyan
Read-Host "Press Enter to continue"

try {
    cloudflared tunnel login
    Write-Host "✅ Cloudflare authentication complete" -ForegroundColor Green
} catch {
    Write-Host "❌ Authentication failed" -ForegroundColor Red
    exit 1
}

# Step 3: Create tunnel
Write-Host ""
Write-Host "[3/5] Creating deer-hunting-app tunnel..." -ForegroundColor Yellow
try {
    $tunnelOutput = cloudflared tunnel create deer-hunting-app
    Write-Host "✅ Tunnel created successfully" -ForegroundColor Green
    Write-Host $tunnelOutput -ForegroundColor Cyan
    
    # Extract tunnel ID from output
    $tunnelId = ($tunnelOutput | Select-String "Created tunnel .* with id: (.*)").Matches[0].Groups[1].Value
    Write-Host "📝 Tunnel ID: $tunnelId" -ForegroundColor Yellow
} catch {
    Write-Host "⚠️ Tunnel might already exist" -ForegroundColor Yellow
}

# Step 4: Create config file
Write-Host ""
Write-Host "[4/5] Creating tunnel configuration..." -ForegroundColor Yellow
$configPath = "$env:USERPROFILE\.cloudflared\config.yml"
$configDir = Split-Path $configPath

if (!(Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null
}

$configContent = @"
# Cloudflare Tunnel Configuration for Deer Hunting App
tunnel: deer-hunting-app
credentials-file: $env:USERPROFILE\.cloudflared\$tunnelId.json

ingress:
  - service: http://localhost:8501
"@

$configContent | Out-File -FilePath $configPath -Encoding UTF8
Write-Host "✅ Configuration file created: $configPath" -ForegroundColor Green

# Step 5: Test setup
Write-Host ""
Write-Host "[5/5] Testing tunnel setup..." -ForegroundColor Yellow
try {
    cloudflared tunnel list
    Write-Host "✅ Tunnel setup complete!" -ForegroundColor Green
} catch {
    Write-Host "❌ Setup verification failed" -ForegroundColor Red
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "🎯 SETUP COMPLETE! 🎯" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Double-click 'start-deer-app.bat' to launch your app" -ForegroundColor White
Write-Host "2. Open the URL on your iPhone Safari" -ForegroundColor White
Write-Host "3. Add to home screen for app-like experience" -ForegroundColor White
Write-Host ""
Write-Host "🦌 Happy hunting with satellite intelligence! 🛰️" -ForegroundColor Green
Write-Host ""
Read-Host "Press Enter to exit"
