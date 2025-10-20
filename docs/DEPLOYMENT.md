# 🚀 Deployment Documentation

## Overview
Complete deployment guide for the deer prediction application across different environments and platforms.

## 📋 Quick Start

### Local Development
```bash
# Start backend
cd backend
python main.py

# Start frontend (new terminal)
streamlit run frontend/app.py
### Docker Deployment (Recommended)
docker-compose up --build
docker-compose up -d --build
```bash
# Build and start all services


# Background deployment
# View logs

# View logs
docker-compose logs -f
```

## 🐳 Docker Containerized System

### What's Included
- **Backend Container**: FastAPI server with all prediction endpoints
- **Frontend Container**: Streamlit web interface with enhanced visualizations
- **Redis Container**: Caching and session management
- **Persistent Storage**: Data volumes for scouting observations

### Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │     Redis       │
│   Streamlit     │◄──►│    FastAPI      │◄──►│    Cache        │
│   Port: 8501    │    │   Port: 8000    │    │   Port: 6379    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Data Storage  │
                    │    Volumes      │
                    └─────────────────┘
```

### Docker Services
```yaml
# docker-compose.yml structure
version: '3.8'
services:
  backend:
    build: .
    ports: ["8000:8000"]
    volumes: ["./scouting_data:/app/scouting_data"]
    
  frontend:
    build: ./frontend
    ports: ["8501:8501"]
    depends_on: [backend]
    
  redis:
    image: redis:alpine
    volumes: ["redis_data:/data"]
```

## 🌐 Production Deployment Options

### 1. Cloudflare Tunnel (Current Production)
**Status**: ✅ **DEPLOYED & OPERATIONAL**

**Configuration**:
- **Domain**: https://app.deerpredictapp.org
- **Security**: Password protected (DeerHunter2025!)
- **SSL**: Automatic HTTPS via Cloudflare
- **Status**: Production ready

**Setup Process**:
```bash
# Install Cloudflare tunnel
# Windows: Download cloudflared.exe
# Linux: curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb

# Authenticate with Cloudflare
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create deer-prediction-app

# Configure tunnel (see docker/cloudflare-config.yml)
cloudflared tunnel route dns deer-prediction-app app.deerpredictapp.org

# Start tunnel
cloudflared tunnel run deer-prediction-app
```

**Benefits**:
- No port forwarding required
- Automatic SSL certificates
- DDoS protection
- Global CDN acceleration

### 2. Railway Deployment
**Status**: 📋 **AVAILABLE OPTION**

Railway provides simple containerized deployment with automatic scaling.

**Setup Steps**:
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize project
railway init

# Deploy
railway up
```

**Configuration Requirements**:
- `railway.json` configuration file
- Environment variables for API keys
- Database connection strings
- Port configuration (Railway auto-assigns)

**Benefits**:
- Automatic scaling
- Built-in monitoring
- GitHub integration
- Free tier available

### 3. Google Cloud Platform
**Status**: 📋 **AVAILABLE OPTION**

Deploy using Google Cloud Run for serverless container deployment.

**Setup Process**:
```bash
# Build and tag image
docker build -t deer-prediction-app .
docker tag deer-prediction-app gcr.io/[PROJECT-ID]/deer-prediction-app

# Push to Container Registry
docker push gcr.io/[PROJECT-ID]/deer-prediction-app

# Deploy to Cloud Run
gcloud run deploy deer-prediction-app \
    --image gcr.io/[PROJECT-ID]/deer-prediction-app \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated
```

**Benefits**:
- Pay-per-use pricing
- Automatic scaling to zero
- Global load balancing
- Integrated monitoring

### 4. AWS Deployment
**Status**: 📋 **AVAILABLE OPTION**

Deploy using AWS ECS with Fargate for serverless containers.

**Architecture**:
- **ECS Fargate**: Serverless container hosting
- **ALB**: Application Load Balancer
- **RDS**: Managed database (if needed)
- **CloudFront**: Global CDN

## 🔒 Security Configuration

### Authentication System
```python
# Streamlit password protection
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if password == "DeerHunter2025!":
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Incorrect password")
        return False
    return True
```

### SSL/TLS Configuration
- **Cloudflare**: Automatic SSL certificates
- **Manual Setup**: Use Let's Encrypt or commercial certificates
- **Docker**: Configure reverse proxy (nginx) for SSL termination

### Environment Variables
```bash
# Required environment variables
GOOGLE_MAPS_API_KEY=your_api_key_here
WEATHER_API_KEY=your_weather_key_here
ENABLE_LIDAR=0
DEBUG_MODE=0
PRODUCTION_MODE=1
```

## 📊 Monitoring & Analytics

### Health Checks
```python
# Backend health endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": "connected",
            "cache": "connected",
            "ml_models": "loaded"
        }
    }
```

### Performance Monitoring
- **Response Times**: API endpoint monitoring
- **Error Rates**: Automatic error tracking
- **Resource Usage**: CPU/Memory monitoring
- **User Analytics**: Session tracking and usage patterns

### Logging Configuration
```python
# Structured logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

## 🔧 Troubleshooting

### Common Issues

1. **Backend Connection Failed**
   ```bash
   # Check backend service
    docker-compose -f docker/docker-compose.yml logs backend
   
   # Restart services
    docker-compose -f docker/docker-compose.yml restart backend
   ```

2. **Frontend Not Loading**
   ```bash
   # Check frontend logs
    docker-compose -f docker/docker-compose.yml logs frontend
   
   # Verify backend connectivity
   curl http://localhost:8000/health
   ```

3. **Database Connection Issues**
   ```bash
   # Check volume mounts
   docker volume ls
   
   # Inspect volume
   docker volume inspect deer_pred_app_scouting_data
   ```

4. **Performance Issues**
   ```bash
   # Monitor resource usage
   docker stats
   
   # Check system resources
   htop  # Linux
   Task Manager  # Windows
   ```

### Debug Commands
```bash
# View all container logs
docker-compose -f docker/docker-compose.yml logs -f

# Access container shell
docker-compose -f docker/docker-compose.yml exec backend /bin/bash

# Check network connectivity
docker-compose -f docker/docker-compose.yml exec frontend ping backend

# Restart specific service
docker-compose -f docker/docker-compose.yml restart frontend
```

## 📈 Scaling Considerations

### Horizontal Scaling
- **Load Balancer**: nginx or AWS ALB
- **Multiple Instances**: Docker Swarm or Kubernetes
- **Database**: Separate database server or managed service
- **Cache**: Redis cluster or managed cache service

### Vertical Scaling
- **CPU**: Increase container CPU limits
- **Memory**: Allocate more RAM to containers
- **Storage**: Use faster SSD storage
- **Network**: Optimize network configuration

### Performance Optimization
- **Caching**: Implement Redis caching for predictions
- **CDN**: Use CloudFront or Cloudflare for static assets
- **Database**: Optimize queries and add indexes
- **ML Models**: Model quantization and optimization

## 🎯 Deployment Checklist

### Pre-Deployment
- [ ] Environment variables configured
- [ ] SSL certificates obtained
- [ ] Database migrations completed
- [ ] Security audit passed
- [ ] Performance testing completed

### Deployment
- [ ] Build Docker images
- [ ] Run health checks
- [ ] Deploy to staging environment
- [ ] Validate all functionality
- [ ] Deploy to production
- [ ] Monitor for errors

### Post-Deployment
- [ ] Verify all services running
- [ ] Check application logs
- [ ] Test critical user paths
- [ ] Monitor performance metrics
- [ ] Update documentation

---

## 📚 Related Documentation
- **[Testing](TESTING.md)** - Validation and testing procedures
- **[Architecture](ARCHITECTURE.md)** - System design and components
- **[Security](SECURITY.md)** - Security configuration and best practices
- **[Analytics](../ANALYTICS_README.md)** - Performance monitoring setup

---

*Last Updated: August 25, 2025*  
*Production URL: https://app.deerpredictapp.org*  
*Status: ✅ FULLY OPERATIONAL*
