# Cloudflare Tunnel Service Manager
# Manage the cloudflared Windows service

param(
    [Parameter(Position=0)]
    [ValidateSet('start', 'stop', 'restart', 'status', 'logs', 'uninstall')]
    [string]$Action = 'status'
)

Write-Host "🌐 Cloudflare Tunnel Service Manager" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green
Write-Host ""

function Show-Status {
    try {
        $service = Get-Service -Name "cloudflared" -ErrorAction Stop
        
        Write-Host "📊 Service Status:" -ForegroundColor Yellow
        Write-Host "   Name: $($service.Name)" -ForegroundColor Gray
        Write-Host "   Display Name: $($service.DisplayName)" -ForegroundColor Gray
        Write-Host "   Status: $($service.Status)" -ForegroundColor $(if ($service.Status -eq "Running") { "Green" } else { "Red" })
        Write-Host "   Startup Type: $($service.StartType)" -ForegroundColor Gray
        Write-Host ""
        
        if ($service.Status -eq "Running") {
            Write-Host "✅ Tunnel is running!" -ForegroundColor Green
            Write-Host "🌐 App accessible at: https://app.deerpredictapp.org" -ForegroundColor Cyan
        } else {
            Write-Host "⚠️  Tunnel is not running" -ForegroundColor Yellow
            Write-Host "   Run: .\manage-cloudflare.ps1 start" -ForegroundColor Cyan
        }
        
    } catch {
        Write-Host "❌ Cloudflare service not installed" -ForegroundColor Red
        Write-Host "   Run install-cloudflare-service.ps1 as Administrator" -ForegroundColor Yellow
    }
}

function Start-Tunnel {
    Write-Host "🚀 Starting Cloudflare tunnel..." -ForegroundColor Yellow
    try {
        Start-Service -Name "cloudflared"
        Start-Sleep -Seconds 3
        Show-Status
    } catch {
        Write-Host "❌ Failed to start service: $_" -ForegroundColor Red
    }
}

function Stop-Tunnel {
    Write-Host "🛑 Stopping Cloudflare tunnel..." -ForegroundColor Yellow
    try {
        Stop-Service -Name "cloudflared"
        Start-Sleep -Seconds 2
        Write-Host "✅ Tunnel stopped" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to stop service: $_" -ForegroundColor Red
    }
}

function Restart-Tunnel {
    Write-Host "🔄 Restarting Cloudflare tunnel..." -ForegroundColor Yellow
    Stop-Tunnel
    Start-Sleep -Seconds 2
    Start-Tunnel
}

function Show-Logs {
    Write-Host "📋 Cloudflare Tunnel Logs" -ForegroundColor Yellow
    Write-Host "=========================" -ForegroundColor Yellow
    Write-Host ""
    
    # Windows service logs are in Event Viewer, but cloudflared also has its own log location
    $logPath = "$env:USERPROFILE\.cloudflared\cloudflared.log"
    
    if (Test-Path $logPath) {
        Write-Host "📄 Log file: $logPath" -ForegroundColor Gray
        Write-Host ""
        Get-Content $logPath -Tail 50 | Write-Host
    } else {
        Write-Host "⚠️  Log file not found at: $logPath" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Checking Event Viewer..." -ForegroundColor Gray
        Get-EventLog -LogName Application -Source "cloudflared" -Newest 10 -ErrorAction SilentlyContinue | Format-Table -AutoSize
    }
}

function Uninstall-Service {
    Write-Host "⚠️  This will uninstall the Cloudflare service" -ForegroundColor Yellow
    $confirm = Read-Host "Are you sure? (yes/no)"
    
    if ($confirm -eq "yes") {
        Write-Host ""
        Write-Host "🛑 Stopping service..." -ForegroundColor Yellow
        Stop-Service -Name "cloudflared" -ErrorAction SilentlyContinue
        
        Write-Host "🗑️  Uninstalling service..." -ForegroundColor Yellow
        Write-Host "   This requires Administrator privileges" -ForegroundColor Gray
        
        # Check if admin
        $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
        
        if ($isAdmin) {
            cloudflared service uninstall
            Write-Host "✅ Service uninstalled" -ForegroundColor Green
        } else {
            Write-Host "❌ Run this command as Administrator:" -ForegroundColor Red
            Write-Host "   cloudflared service uninstall" -ForegroundColor Cyan
        }
    } else {
        Write-Host "Cancelled" -ForegroundColor Gray
    }
}

# Execute the requested action
switch ($Action) {
    'start'     { Start-Tunnel }
    'stop'      { Stop-Tunnel }
    'restart'   { Restart-Tunnel }
    'status'    { Show-Status }
    'logs'      { Show-Logs }
    'uninstall' { Uninstall-Service }
}

Write-Host ""
Write-Host "💡 Usage: .\manage-cloudflare.ps1 [start|stop|restart|status|logs|uninstall]" -ForegroundColor Cyan
Write-Host ""
