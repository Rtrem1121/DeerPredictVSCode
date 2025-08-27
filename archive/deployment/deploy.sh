#!/bin/bash

# Docker deployment script for Deer Prediction App

set -e  # Exit on any error

echo "🐳 Starting Docker deployment..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please copy .env.example to .env and configure."
    exit 1
fi

# Source environment variables
source .env

# Check required environment variables
if [ -z "$OPENWEATHERMAP_API_KEY" ]; then
    echo "❌ OPENWEATHERMAP_API_KEY not set in .env file"
    exit 1
fi

# Function to check if container is healthy
check_health() {
    local service=$1
    local max_attempts=30
    local attempt=1
    
    echo "⏳ Waiting for $service to be healthy..."
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose ps $service | grep -q "healthy"; then
            echo "✅ $service is healthy"
            return 0
        fi
        
        echo "Attempt $attempt/$max_attempts: $service not ready yet..."
        sleep 10
        attempt=$((attempt + 1))
    done
    
    echo "❌ $service failed to become healthy"
    return 1
}

# Development deployment
deploy_dev() {
    echo "🔧 Deploying for development..."
    
    # Build and start containers
    docker-compose build
    docker-compose up -d
    
    # Check health
    check_health backend
    check_health frontend
    
    echo "🎉 Development deployment complete!"
    echo "📱 Frontend: http://localhost:8501"
    echo "🔧 Backend API: http://localhost:8000/docs"
}

# Production deployment
deploy_prod() {
    echo "🚀 Deploying for production..."
    
    # Build and start containers with production overrides
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml build
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
    
    # Check health
    check_health backend
    check_health frontend
    
    echo "🎉 Production deployment complete!"
    echo "🌐 Application: http://localhost"
}

# Cleanup function
cleanup() {
    echo "🧹 Cleaning up..."
    docker-compose down
    docker system prune -f
    echo "✅ Cleanup complete"
}

# Show logs
show_logs() {
    docker-compose logs -f
}

# Show status
show_status() {
    echo "📊 Container Status:"
    docker-compose ps
    echo ""
    echo "🏥 Health Status:"
    docker-compose exec backend curl -s http://localhost:8000/health | jq . || echo "Backend not accessible"
}

# Main script logic
case "${1:-dev}" in
    "dev")
        deploy_dev
        ;;
    "prod")
        deploy_prod
        ;;
    "cleanup")
        cleanup
        ;;
    "logs")
        show_logs
        ;;
    "status")
        show_status
        ;;
    *)
        echo "Usage: $0 {dev|prod|cleanup|logs|status}"
        echo "  dev     - Deploy for development (default)"
        echo "  prod    - Deploy for production"
        echo "  cleanup - Stop containers and cleanup"
        echo "  logs    - Show container logs"
        echo "  status  - Show container status"
        exit 1
        ;;
esac
