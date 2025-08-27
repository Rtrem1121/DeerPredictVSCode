# 🦌 DEER PREDICTION APP - AI AGENT GUIDELINES

## Project Overview
Advanced deer prediction system with camera placement algorithms, wind analysis, and satellite integration. Built for serious hunters who want data-driven scouting intelligence.

**Key Features:**
- Enhanced camera placement with 89.1% confidence scores
- Mature buck specialized algorithms  
- Real-time wind direction analysis
- GPS coordinate precision
- Streamlit mobile-optimized frontend
- Railway deployment ready

## 🛠️ Development Environment

### Quick Start Commands
```bash
# Backend Development
cd backend && python app.py

# Frontend Development  
cd frontend && streamlit run app.py --server.port 8501

# Full System Test
python comprehensive_system_test.py

# Docker Development
docker-compose up --build
```

### Python Environment Setup
```bash
# Configure Python environment first
python configure_python_environment.py

# Install dependencies
pip install -r analytics_requirements.txt
pip install streamlit requests python-dotenv

# Google Earth Engine (if using satellite features)
pip install earthengine-api
```

## 🎯 Core Algorithms & Code Style

### Prediction Confidence Standards
- **Camera placement confidence:** Target 85%+ for deployment
- **Mature buck algorithms:** Use specialized scoring (current: 89.1%)
- **Wind analysis:** Real-time integration required
- **GPS precision:** 6+ decimal places for camera coordinates

### Code Conventions
- **Python style:** Follow existing `predict_deer_movement()` patterns
- **Streamlit components:** Use `@st.cache_data` for map rendering
- **API integration:** Async patterns for weather/satellite data
- **Error handling:** Hunter-friendly error messages (no tech jargon)

### File Structure Priorities
```
backend/app.py          # Core prediction engine
frontend/app.py         # Streamlit hunting interface  
advanced_camera_placement.py  # Camera algorithm (DO NOT MODIFY core logic)
comprehensive_system_test.py  # Always run before deployment
```

## 🧪 Testing Instructions

### Critical Tests (Run Before Any Deployment)
```bash
# Full system validation (REQUIRED)
python comprehensive_system_test.py

# Algorithm accuracy verification
python prediction_validation_results.py

# Camera placement verification  
python final_satellite_verification.py

# Frontend/backend integration
python debug_integration.py
```

### Testing Standards
- **All 4 core tests must pass** before merging
- **Camera algorithms require 85%+ confidence**
- **Mobile responsive testing on iPhone Safari**
- **GPS coordinate accuracy verification**

## 🚀 Deployment Instructions

### Railway Deployment (Production)
```bash
# Use existing Railway configuration
# Files: Procfile, Dockerfile.railway, railway.json

# Deploy command
railway up

# Environment variables required:
BACKEND_URL=https://your-app.railway.app
PORT=8501
OPENWEATHERMAP_API_KEY=your_key
```

### Local Development
```bash
# Backend
cd backend && python app.py

# Frontend (separate terminal)  
cd frontend && streamlit run app.py --server.port 8501

# Access at: http://localhost:8501
```

## 🦌 Hunting-Specific Context

### Algorithm Priorities
1. **Enhanced Stand #1** - Primary algorithm (89.1% confidence)
2. **Wind direction intelligence** - Critical for scent management
3. **Mature buck patterns** - Specialized behavior modeling
4. **Camera GPS precision** - Exact placement coordinates

### User Experience Focus
- **Mobile-first design** for field use on iPhone
- **GPS integration** for real-time location detection
- **Hunter-friendly language** (avoid technical jargon)
- **Offline capability** after initial load

### Data Sources
- **Weather API:** OpenWeatherMap integration
- **Satellite data:** Google Earth Engine (optional)
- **Terrain analysis:** USGS elevation data
- **Historical patterns:** Local deer movement data

## 🔧 Common Tasks

### Adding New Prediction Algorithms
1. Create in `backend/` following `predict_deer_movement()` pattern
2. Add to `comprehensive_system_test.py` validation
3. Update confidence thresholds in frontend
4. Test mobile responsiveness

### Modifying Camera Placement
- **DO NOT modify core camera placement logic** without full testing
- Update `advanced_camera_placement.py` carefully
- Always run `prediction_validation_results.py` after changes
- Verify GPS coordinate precision

### Frontend Updates
- Test mobile responsiveness on iPhone Safari
- Verify map interactions (pinch, zoom, tap)
- Check GPS location detection
- Validate "Add to Home Screen" PWA functionality

## 🎯 Pull Request Guidelines

### PR Title Format
`[FEATURE] Brief description` or `[BUG] Fix description`

### Required Checks Before PR
```bash
# Run full test suite
python comprehensive_system_test.py

# Verify confidence scores
python prediction_validation_results.py  

# Test mobile interface
# Open iPhone Safari → Test all functions

# Check deployment readiness
python railway_deployment_setup.py
```

### Hunting App Specific Requirements
- Maintain hunter-focused user experience
- Preserve algorithm confidence levels (85%+ required)
- Test on mobile devices (hunters use phones in field)
- Keep technical complexity hidden from users

## 🦌 Project Philosophy

**This is a tool for serious hunters who want data-driven intelligence.**

- Prioritize accuracy over flashy features
- Mobile experience is critical (used in field)
- GPS precision matters for camera placement
- Keep it simple but powerful
- Honor the hunting tradition while embracing technology

---

*Built for hunters, by hunters. With AI assistance that understands the woods.*
