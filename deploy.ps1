# PowerShell deployment script for Deer Prediction App on Windows

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("dev", "prod", "cleanup", "logs", "status")]
    [string]$Action = "dev"
)

$ErrorActionPreference = "Stop"

Write-Host "🐳 Starting Docker deployment..." -ForegroundColor Blue

# Check if .env file exists
if (!(Test-Path ".env")) {
    Write-Host "❌ .env file not found. Please copy .env.example to .env and configure." -ForegroundColor Red
    exit 1
}

# Load environment variables from .env file
Get-Content ".env" | ForEach-Object {
    if ($_ -match "^([^#][^=]+)=(.*)$") {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
    }
}

# Check required environment variables
if ([string]::IsNullOrEmpty($env:OPENWEATHERMAP_API_KEY)) {
    Write-Host "❌ OPENWEATHERMAP_API_KEY not set in .env file" -ForegroundColor Red
    exit 1
}

# Function to check if container is healthy
function Test-ContainerHealth {
    param([string]$ServiceName)
    
    $maxAttempts = 30
    $attempt = 1
    
    Write-Host "⏳ Waiting for $ServiceName to be healthy..." -ForegroundColor Yellow
    
    do {
        try {
            $status = docker-compose ps $ServiceName
            if ($status -match "healthy") {
                Write-Host "✅ $ServiceName is healthy" -ForegroundColor Green
                return $true
            }
        }
        catch {
            # Container might not be up yet
        }
        
        Write-Host "Attempt $attempt/$maxAttempts`: $ServiceName not ready yet..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
        $attempt++
    } while ($attempt -le $maxAttempts)
    
    Write-Host "❌ $ServiceName failed to become healthy" -ForegroundColor Red
    return $false
}

# Development deployment
function Deploy-Dev {
    Write-Host "🔧 Deploying for development..." -ForegroundColor Blue
    
    # Build and start containers
    docker-compose build
    docker-compose up -d
    
    # Check health
    if (!(Test-ContainerHealth "backend")) { exit 1 }
    if (!(Test-ContainerHealth "frontend")) { exit 1 }
    
    Write-Host "🎉 Development deployment complete!" -ForegroundColor Green
    Write-Host "📱 Frontend: http://localhost:8501" -ForegroundColor Cyan
    Write-Host "🔧 Backend API: http://localhost:8000/docs" -ForegroundColor Cyan
}

# Production deployment
function Deploy-Prod {
    Write-Host "🚀 Deploying for production..." -ForegroundColor Blue
    
    # Build and start containers with production overrides
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml build
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
    
    # Check health
    if (!(Test-ContainerHealth "backend")) { exit 1 }
    if (!(Test-ContainerHealth "frontend")) { exit 1 }
    
    Write-Host "🎉 Production deployment complete!" -ForegroundColor Green
    Write-Host "🌐 Application: http://localhost" -ForegroundColor Cyan
}

# Cleanup function
function Invoke-Cleanup {
    Write-Host "🧹 Cleaning up..." -ForegroundColor Yellow
    docker-compose down
    docker system prune -f
    Write-Host "✅ Cleanup complete" -ForegroundColor Green
}

# Show logs
function Show-Logs {
    docker-compose logs -f
}

# Show status
function Show-Status {
    Write-Host "📊 Container Status:" -ForegroundColor Blue
    docker-compose ps
    Write-Host ""
    Write-Host "🏥 Health Status:" -ForegroundColor Blue
    try {
        $healthCheck = docker-compose exec backend curl -s http://localhost:8000/health
        $healthCheck | ConvertFrom-Json | ConvertTo-Json -Depth 10
    }
    catch {
        Write-Host "Backend not accessible" -ForegroundColor Red
    }
}

# Main script logic
switch ($Action) {
    "dev" { Deploy-Dev }
    "prod" { Deploy-Prod }
    "cleanup" { Invoke-Cleanup }
    "logs" { Show-Logs }
    "status" { Show-Status }
    default {
        Write-Host "Usage: .\deploy.ps1 {dev|prod|cleanup|logs|status}" -ForegroundColor Yellow
        Write-Host "  dev     - Deploy for development (default)" -ForegroundColor White
        Write-Host "  prod    - Deploy for production" -ForegroundColor White
        Write-Host "  cleanup - Stop containers and cleanup" -ForegroundColor White
        Write-Host "  logs    - Show container logs" -ForegroundColor White
        Write-Host "  status  - Show container status" -ForegroundColor White
    }
}
