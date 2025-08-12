# Docker Deployment Guide

## 🐳 Complete Containerized Deer Prediction System

Your deer prediction app with scouting system is fully containerized and ready for deployment!

## ✅ What's Included

### Backend Container
- FastAPI server with all prediction endpoints
- Complete scouting system with 8 observation types
- Persistent data storage for scouting observations
- Health checks and monitoring
- Vermont hunting hours compliance

### Frontend Container  
- Streamlit web interface
- Enhanced heatmap visualization
- Map-based interaction
- Vermont hunting time restrictions

### Persistence
- `scouting_data` volume for scouting observations
- `redis_data` volume for caching (optional)
- Configuration and logs mounted from host

## 🚀 Quick Start

### Start Full Application
```bash
# Start all services (backend, frontend, redis)
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Access the Application
- **Frontend**: http://localhost:8501 (Streamlit interface)
- **Backend API**: http://localhost:8000 (FastAPI docs at /docs)
- **Health Check**: http://localhost:8000/health

### Stop Application
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ deletes scouting data)
docker-compose down -v
```

## 🎯 Scouting System Testing

### Test Scouting API (in container)
```bash
# Check available observation types
curl http://localhost:8000/scouting/types

# Add a fresh scrape observation
curl -X POST "http://localhost:8000/scouting/add_observation" \
  -H "Content-Type: application/json" \
  -d '{
    "lat": 44.5588,
    "lon": -72.5778,
    "observation_type": "Fresh Scrape",
    "confidence": 8,
    "scrape_details": {
      "size": "Large",
      "freshness": "Very Fresh",
      "licking_branch": true,
      "multiple_scrapes": false
    },
    "notes": "Large fresh scrape with strong scent"
  }'

# Retrieve observations in area
curl "http://localhost:8000/scouting/observations?lat=44.5588&lon=-72.5778&radius_miles=5"

# Get area analytics
curl "http://localhost:8000/scouting/analytics?lat=44.5588&lon=-72.5778&radius_miles=5"
```

## 📊 Container Resources

### Default Limits
- **Backend**: 1GB RAM, 0.5 CPU cores
- **Frontend**: 512MB RAM, 0.3 CPU cores  
- **Redis**: 128MB RAM, 0.1 CPU cores

### Adjust for Production
Edit `docker-compose.yml` to modify resource limits:
```yaml
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '1.0'
```

## 🔧 Environment Variables

### Backend Configuration
```bash
# Set in docker-compose.yml or .env file
OPENWEATHERMAP_API_KEY=your_api_key_here
LOG_LEVEL=INFO
ENABLE_LIDAR=0  # Set to 1 to enable LiDAR features
```

### Frontend Configuration
```bash
BACKEND_URL=http://backend:8000  # Internal container communication
```

## 💾 Data Persistence

### Scouting Data
- Stored in `scouting_data` Docker volume
- Survives container restarts
- JSON format for easy backup/restore

### Backup Scouting Data
```bash
# Copy data from container
docker cp deer_pred_app-backend-1:/app/backend/scouting_data ./backup_scouting_data

# Restore data to container
docker cp ./backup_scouting_data deer_pred_app-backend-1:/app/backend/scouting_data
```

## 🏭 Production Deployment

### Docker Swarm
```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml deer-pred

# Scale services
docker service scale deer-pred_backend=2
```

### Kubernetes
1. Convert compose file: `kompose convert`
2. Apply manifests: `kubectl apply -f .`
3. Expose services: `kubectl expose deployment backend --type=LoadBalancer`

### Cloud Deployment
- **AWS**: Use ECS with Fargate
- **Azure**: Use Container Instances
- **GCP**: Use Cloud Run
- **Digital Ocean**: Use App Platform

## 🔍 Monitoring & Debugging

### Health Checks
```bash
# Backend health
curl http://localhost:8000/health

# Frontend health (if available)
curl http://localhost:8501/_stcore/health
```

### View Logs
```bash
# Live logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Specific service
docker-compose logs backend
```

### Debug Container
```bash
# Enter backend container
docker-compose exec backend bash

# Check scouting data
docker-compose exec backend ls -la /app/backend/scouting_data/

# Check Python environment
docker-compose exec backend python -c "import sys; print(sys.path)"
```

## 🔐 Security Notes

### Production Security
1. **Change default ports** - Map to non-standard ports
2. **Add reverse proxy** - Use nginx/traefik with SSL
3. **Set secrets** - Use Docker secrets for API keys
4. **Network isolation** - Use custom networks
5. **Update base images** - Regular security updates

### Example Secure Deployment
```yaml
# Add to docker-compose.yml
secrets:
  openweather_api_key:
    file: ./secrets/openweather_key.txt

services:
  backend:
    secrets:
      - openweather_api_key
    environment:
      - OPENWEATHERMAP_API_KEY_FILE=/run/secrets/openweather_api_key
```

## ✅ Validation Checklist

- [ ] Backend container starts and passes health check
- [ ] Frontend container starts and loads interface
- [ ] Scouting API endpoints respond correctly
- [ ] Data persists across container restarts
- [ ] Prediction enhancement works with scouting data
- [ ] Resource limits appropriate for environment
- [ ] Logs are accessible and informative
- [ ] Backup/restore procedures tested

## 🆘 Troubleshooting

### Common Issues

**Container won't start**
```bash
# Check logs
docker-compose logs backend

# Check image build
docker-compose build --no-cache backend
```

**Scouting data not persisting**
```bash
# Check volume mount
docker volume inspect deer_pred_app_scouting_data

# Check directory permissions
docker-compose exec backend ls -la /app/backend/scouting_data/
```

**API not responding**
```bash
# Check if container is running
docker-compose ps

# Check port mapping
docker-compose port backend 8000

# Check internal connectivity
docker-compose exec frontend curl http://backend:8000/health
```

## 📈 Performance Optimization

### For Large Datasets
1. Add Redis caching layer
2. Implement database backend (PostgreSQL)
3. Use connection pooling
4. Add CDN for static assets
5. Implement API rate limiting

### Production Scaling
1. Horizontal scaling with load balancer
2. Database clustering
3. Separate prediction workers
4. Cache frequently requested data
5. Implement monitoring (Prometheus/Grafana)

---

🎯 **Your deer prediction system is now production-ready!** 

The complete scouting system works seamlessly in Docker containers with persistent data storage and full API functionality.
