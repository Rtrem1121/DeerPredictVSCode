# Cloudflare Tunnel - Install as Windows Service
# Run this script as Administrator

Write-Host "Installing Cloudflare Tunnel as Windows Service" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green
Write-Host ""

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator" -ForegroundColor Red
    Write-Host ""
    Write-Host "Right-click PowerShell and select 'Run as Administrator', then run:" -ForegroundColor Yellow
    Write-Host "   cd C:\Users\Rich\deer_pred_app" -ForegroundColor Cyan
    Write-Host "   .\install-cloudflare-service.ps1" -ForegroundColor Cyan
    Write-Host ""
    pause
    exit 1
}

# Change to app directory
Set-Location "C:\Users\Rich\deer_pred_app"

Write-Host "Working directory: $(Get-Location)" -ForegroundColor Yellow
Write-Host ""

# Stop any running cloudflared processes
Write-Host "Stopping any existing cloudflared processes..." -ForegroundColor Yellow
Get-Process -Name "cloudflared" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

# Uninstall existing service if present
Write-Host "Checking for existing service..." -ForegroundColor Yellow
try {
    cloudflared service uninstall 2>$null
    Write-Host "   Removed existing service" -ForegroundColor Gray
} catch {
    Write-Host "   No existing service found" -ForegroundColor Gray
}

Start-Sleep -Seconds 2

# Install the service
Write-Host ""
Write-Host "Installing cloudflared service..." -ForegroundColor Yellow
cloudflared service install

if ($LASTEXITCODE -eq 0) {
    Write-Host "SUCCESS: Service installed successfully!" -ForegroundColor Green
    
    # Start the service
    Write-Host ""
    Write-Host "Starting cloudflare tunnel service..." -ForegroundColor Yellow
    Start-Sleep -Seconds 2
    
    Start-Service -Name "cloudflared"
    
    # Check service status
    Start-Sleep -Seconds 3
    $service = Get-Service -Name "cloudflared"
    
    if ($service.Status -eq "Running") {
        Write-Host "SUCCESS: Cloudflare tunnel is now running!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Your app should be accessible at:" -ForegroundColor Cyan
        Write-Host "   https://app.deerpredictapp.org" -ForegroundColor Green
        Write-Host ""
        Write-Host "Service Details:" -ForegroundColor Yellow
        Write-Host "   Name: cloudflared" -ForegroundColor Gray
        Write-Host "   Status: $($service.Status)" -ForegroundColor Gray
        Write-Host "   Startup: $($service.StartType)" -ForegroundColor Gray
        Write-Host ""
        Write-Host "NOTE: The tunnel will start automatically when Windows boots" -ForegroundColor Cyan
    } else {
        Write-Host "WARNING: Service installed but not running. Status: $($service.Status)" -ForegroundColor Yellow
        Write-Host "   Try: Start-Service -Name cloudflared" -ForegroundColor Cyan
    }
    
} else {
    Write-Host "ERROR: Service installation failed" -ForegroundColor Red
    Write-Host "   Error code: $LASTEXITCODE" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host ""
pause
