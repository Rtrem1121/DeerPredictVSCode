# Analytics Dashboard Documentation

## 🦌 Vermont Deer Prediction Analytics System

The analytics system provides comprehensive real-time monitoring and historical analysis of the deer prediction system performance. This document covers the complete analytics infrastructure including data collection, performance monitoring, dashboard API, and frontend visualization.

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Components](#components)
4. [Installation & Setup](#installation--setup)
5. [Usage Guide](#usage-guide)
6. [API Reference](#api-reference)
7. [Dashboard Features](#dashboard-features)
8. [Configuration](#configuration)
9. [Troubleshooting](#troubleshooting)
10. [Development](#development)

---

## 🎯 System Overview

The analytics system tracks and visualizes:

- **Prediction Analytics**: Success rates, confidence scores, usage patterns
- **Performance Metrics**: Response times, CPU/memory usage, system health
- **Configuration Tracking**: Parameter changes and their impact
- **User Behavior**: Request patterns and geographic distribution
- **System Monitoring**: Real-time alerts and performance trends

### Key Features

- ✅ **Real-time Data Collection**: SQLite database with analytics data
- ✅ **Performance Monitoring**: System resource tracking with alerts
- ✅ **REST API**: FastAPI backend serving analytics data
- ✅ **Interactive Dashboard**: HTML5 frontend with Chart.js visualizations
- ✅ **Configuration Integration**: Tracks parameter changes and impacts
- ✅ **Hot-reload Support**: Real-time configuration updates
- ✅ **Alert System**: Performance threshold monitoring

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Analytics System                         │
├─────────────────────────────────────────────────────────────┤
│  Frontend Dashboard (Port 8002)                            │
│  ├── HTML5 + Chart.js                                      │
│  ├── Real-time API communication                           │
│  └── Interactive visualizations                            │
├─────────────────────────────────────────────────────────────┤
│  Backend API (Port 8001)                                   │
│  ├── FastAPI REST endpoints                                │
│  ├── Pydantic data validation                              │
│  └── CORS-enabled for frontend                             │
├─────────────────────────────────────────────────────────────┤
│  Data Layer                                                 │
│  ├── SQLite analytics database                             │
│  ├── Performance monitoring                                │
│  └── Configuration tracking                                │
├─────────────────────────────────────────────────────────────┤
│  Integration Layer                                          │
│  ├── Prediction system hooks                               │
│  ├── Configuration manager integration                     │
│  └── System performance collectors                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Components

### 1. Data Collector (`analytics/data_collector.py`)

**Purpose**: Central data collection and storage system

**Key Classes**:
- `AnalyticsCollector`: Main data collection orchestrator
- `PredictionRecord`: Prediction request/response data model
- `PerformanceMetric`: System performance measurement
- `ConfigurationChange`: Configuration parameter change tracking

**Database Schema**:
```sql
-- Predictions table
predictions (
    prediction_id, timestamp, latitude, longitude, season,
    weather_conditions, time_of_day, stand_rating, confidence_score,
    mature_buck_score, response_time_ms, processing_time_ms,
    config_version, config_environment, actual_success,
    user_feedback_score, notes
)

-- Performance metrics table
performance_metrics (
    metric_id, timestamp, metric_type, value, details
)

-- Configuration changes table
configuration_changes (
    change_id, timestamp, parameter_path, old_value,
    new_value, changed_by, reason
)

-- Analytics summary table
analytics_summary (
    summary_date, total_predictions, avg_confidence_score,
    avg_response_time_ms, success_rate, unique_users, config_changes
)
```

### 2. Performance Monitor (`analytics/performance_monitor.py`)

**Purpose**: Real-time system performance monitoring with alerts

**Key Classes**:
- `PerformanceMonitor`: Continuous system monitoring
- `PerformanceAlert`: Alert notification system
- `SystemHealth`: Current system status snapshot

**Monitored Metrics**:
- CPU usage percentage
- Memory usage percentage
- Disk usage percentage
- Network connections
- Average response time
- Predictions per minute
- Error rate percentage

**Alert Thresholds**:
```python
alert_thresholds = {
    'cpu_usage_warning': 70.0,      # 70% CPU usage
    'cpu_usage_critical': 85.0,     # 85% CPU usage
    'memory_usage_warning': 75.0,   # 75% memory usage
    'memory_usage_critical': 90.0,  # 90% memory usage
    'response_time_warning': 2000.0,  # 2 second response
    'response_time_critical': 5000.0, # 5 second response
    'error_rate_warning': 5.0,      # 5% error rate
    'error_rate_critical': 15.0     # 15% error rate
}
```

### 3. Dashboard API (`analytics/dashboard_api.py`)

**Purpose**: FastAPI REST backend serving analytics data

**Key Endpoints**:

```
GET /                           # API status
GET /health                     # Health check
GET /analytics/predictions      # Prediction analytics
GET /analytics/performance      # Performance analytics
GET /monitoring/health          # Current system health
GET /monitoring/metrics         # Performance metrics history
GET /monitoring/summary         # Performance summary stats
GET /config/current            # Current configuration
GET /dashboard/overview        # Comprehensive dashboard data
POST /analytics/update-summary  # Trigger summary update
```

**Response Models**:
- `AnalyticsSummary`: Prediction summary statistics
- `SystemHealthResponse`: Current system health status
- `PerformanceMetric`: Performance measurement data
- `AlertResponse`: Performance alert notifications

### 4. Frontend Dashboard (`frontend/dashboard/index.html`)

**Purpose**: Interactive web dashboard for analytics visualization

**Features**:
- Real-time system health monitoring
- Prediction analytics charts and metrics
- Performance trend visualizations
- Configuration status display
- Auto-refresh capabilities
- Responsive design for mobile/desktop

**Chart Types**:
- Line charts for performance trends
- Doughnut charts for confidence distribution
- Metric cards for key statistics
- Status indicators for system health

---

## 📦 Installation & Setup

### Prerequisites

```bash
# Required Python packages
pip install psutil>=5.9.0
pip install fastapi>=0.104.0
pip install uvicorn[standard]>=0.24.0
pip install pydantic>=2.0.0
pip install numpy>=1.24.0
pip install pandas>=2.0.0
```

### Quick Start

1. **Install Dependencies**:
```bash
cd c:\Users\Rich\deer_pred_app
pip install -r analytics_requirements.txt
```

2. **Run Analytics Integration Test**:
```bash
cd backend
python test_analytics_integration.py
```

3. **Generate Sample Data** (optional):
```bash
python analytics_demo.py
```

4. **Start Dashboard**:
```bash
python start_dashboard.py
```

5. **Access Dashboard**:
- Frontend: http://localhost:8002
- API: http://localhost:8001

---

## 📖 Usage Guide

### Starting the Analytics System

#### Method 1: Integrated Dashboard
```bash
cd backend
python start_dashboard.py
```
This starts both the API backend (port 8001) and frontend server (port 8002).

#### Method 2: API Only
```bash
cd backend
python -m analytics.dashboard_api
```
Starts only the FastAPI backend on port 8001.

#### Method 3: Programmatic Integration
```python
from analytics import (
    get_analytics_collector,
    get_performance_monitor,
    start_performance_monitoring,
    record_prediction_analytics
)

# Initialize analytics
analytics = get_analytics_collector()
monitor = get_performance_monitor()

# Start monitoring
start_performance_monitoring()

# Record prediction data
record_prediction_analytics(
    prediction_id="unique_id",
    request_data={"lat": 44.26, "lon": -72.58, "season": "archery"},
    response_data={"stand_rating": 75.5, "confidence_score": 82.3},
    performance_data={"response_time_ms": 150.0}
)
```

### Dashboard Navigation

1. **Status Bar**: Real-time system overview
   - System status (healthy/warning/critical)
   - CPU and memory usage
   - Average response time
   - Daily prediction count

2. **System Health Card**: Detailed resource monitoring
   - CPU, memory, and disk usage
   - Overall system status
   - Manual refresh capability

3. **Prediction Analytics Card**: Prediction statistics
   - Total predictions
   - Average confidence score
   - Average stand rating
   - Active days count

4. **Performance Trends Chart**: Historical performance
   - CPU and memory usage over time
   - Response time trends
   - Interactive Chart.js visualization

5. **Confidence Distribution Chart**: Prediction confidence analysis
   - Distribution across confidence ranges
   - Doughnut chart visualization
   - Color-coded by confidence level

6. **Configuration Card**: Current system configuration
   - Environment and version information
   - Parameter counts by category
   - Configuration refresh

---

## 🔌 API Reference

### Base URL
```
http://localhost:8001
```

### Authentication
Currently no authentication required (development mode).

### Endpoints

#### GET `/dashboard/overview`
Returns comprehensive dashboard data.

**Response**:
```json
{
  "timestamp": "2025-01-09T20:00:00",
  "system_health": {
    "overall_status": "healthy",
    "cpu_usage": 15.2,
    "memory_usage": 22.1,
    "response_time": 145.3
  },
  "prediction_summary": {
    "total_predictions": 156,
    "avg_confidence": 72.4,
    "avg_rating": 68.7
  },
  "performance_trends": {...},
  "configuration": {
    "environment": "development",
    "version": "1.0.0-dev"
  }
}
```

#### GET `/analytics/predictions`
Get prediction analytics with optional filters.

**Parameters**:
- `days` (int): Number of days to analyze (1-365)
- `season` (string): Filter by season
- `min_confidence` (float): Minimum confidence score

**Response**:
```json
{
  "summary": {
    "total_predictions": 156,
    "avg_confidence": 72.4,
    "avg_rating": 68.7,
    "avg_response_time": 145.3,
    "active_days": 7
  },
  "daily_stats": [...],
  "confidence_distribution": [...],
  "query_period_days": 7
}
```

#### GET `/monitoring/health`
Get current system health status.

**Response**:
```json
{
  "timestamp": "2025-01-09T20:00:00",
  "cpu_usage_percent": 15.2,
  "memory_usage_percent": 22.1,
  "disk_usage_percent": 45.7,
  "response_time_avg_ms": 145.3,
  "predictions_per_minute": 3.2,
  "error_rate_percent": 0.5,
  "overall_status": "healthy"
}
```

#### GET `/monitoring/metrics`
Get performance metrics history.

**Parameters**:
- `hours` (int): Hours of metrics to retrieve (1-168)
- `metric_type` (string): Filter by metric type

**Response**:
```json
[
  {
    "timestamp": "2025-01-09T20:00:00",
    "metric_type": "cpu_usage",
    "value": 15.2
  },
  ...
]
```

#### GET `/config/current`
Get current system configuration.

**Response**:
```json
{
  "metadata": {
    "environment": "development",
    "version": "1.0.0-dev",
    "loaded_at": "2025-01-09T19:00:00"
  },
  "parameters": {
    "mature_buck": {...},
    "distance": {...},
    "terrain": {...},
    "weather": {...},
    "timing": {...},
    "seasonal": {...},
    "stand": {...}
  }
}
```

---

## 📊 Dashboard Features

### Real-time Monitoring
- System health status with color-coded indicators
- Live performance metrics updates every 30 seconds
- Auto-refresh functionality with manual override
- Performance alert indicators

### Historical Analysis
- Prediction trends over customizable time periods
- Performance metrics history with interactive charts
- Confidence score distribution analysis
- Seasonal and temporal pattern identification

### Interactive Visualizations
- Chart.js powered interactive charts
- Responsive design for all screen sizes
- Hover tooltips with detailed information
- Zoom and pan capabilities on trend charts

### Configuration Tracking
- Real-time configuration status
- Parameter change history
- Environment and version tracking
- Hot-reload configuration updates

---

## ⚙️ Configuration

### Analytics Configuration
Analytics behavior is controlled through the main configuration system. Key settings:

```yaml
# config/development.yaml
analytics:
  database_path: "analytics_data/deer_prediction_analytics.db"
  monitoring_interval: 30.0  # seconds
  history_retention_days: 365
  performance_thresholds:
    cpu_warning: 70.0
    cpu_critical: 85.0
    memory_warning: 75.0
    memory_critical: 90.0
    response_time_warning: 2000.0
    response_time_critical: 5000.0
```

### Environment Variables
```bash
# Optional environment configuration
ANALYTICS_DB_PATH=/path/to/analytics.db
ANALYTICS_API_PORT=8001
DASHBOARD_PORT=8002
LOG_LEVEL=INFO
```

### API Configuration
The dashboard API can be configured through code:

```python
# Custom API configuration
from analytics.dashboard_api import app
import uvicorn

# Custom CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Specific origins
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Run with custom settings
uvicorn.run(app, host="0.0.0.0", port=8001)
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Database Connection Errors
```
Error: database is locked
```
**Solution**: Ensure only one analytics process is running, check file permissions.

#### 2. Port Already in Use
```
Error: [Errno 98] Address already in use
```
**Solution**: 
```bash
# Find process using port
netstat -ano | findstr :8001
# Kill process
taskkill /PID <process_id> /F
```

#### 3. Missing Dependencies
```
ImportError: No module named 'psutil'
```
**Solution**:
```bash
pip install -r analytics_requirements.txt
```

#### 4. Frontend Not Loading
- Check that both API (8001) and frontend (8002) servers are running
- Verify CORS configuration allows frontend domain
- Check browser console for JavaScript errors

#### 5. No Analytics Data
- Verify predictions are being recorded with `record_prediction_analytics()`
- Check database file exists and has correct permissions
- Run analytics demo to generate sample data: `python analytics_demo.py`

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Database Inspection

Direct database access:
```bash
sqlite3 analytics_data/deer_prediction_analytics.db
.tables
.schema predictions
SELECT COUNT(*) FROM predictions;
```

---

## 🚀 Development

### Adding New Metrics

1. **Define Metric in Data Collector**:
```python
# analytics/data_collector.py
def record_custom_metric(self, metric_name: str, value: float, details: dict = None):
    metric = PerformanceMetric(
        metric_id=f"{metric_name}_{int(time.time() * 1000)}",
        timestamp=datetime.now(),
        metric_type=metric_name,
        value=value,
        details=details or {}
    )
    self.record_performance_metric(metric)
```

2. **Add API Endpoint**:
```python
# analytics/dashboard_api.py
@app.get("/analytics/custom-metric")
async def get_custom_metric():
    # Implementation here
    pass
```

3. **Update Frontend**:
```javascript
// frontend/dashboard/index.html
async function refreshCustomMetric() {
    const data = await fetchData('/analytics/custom-metric');
    // Update UI
}
```

### Adding New Charts

1. **Create Chart Container** in HTML:
```html
<div class="card">
    <h3>New Chart</h3>
    <div class="chart-container">
        <canvas id="newChart"></canvas>
    </div>
</div>
```

2. **Implement Chart Function**:
```javascript
async function createNewChart() {
    const ctx = document.getElementById('newChart').getContext('2d');
    newChart = new Chart(ctx, {
        type: 'bar',
        data: { /* chart data */ },
        options: { /* chart options */ }
    });
}
```

### Testing New Features

1. **Unit Tests**:
```python
# tests/test_analytics.py
import pytest
from analytics import get_analytics_collector

def test_analytics_collection():
    collector = get_analytics_collector()
    # Test implementation
    assert collector is not None
```

2. **Integration Tests**:
```python
# Run existing integration test
python test_analytics_integration.py
```

3. **API Tests**:
```python
from fastapi.testclient import TestClient
from analytics.dashboard_api import app

client = TestClient(app)
response = client.get("/dashboard/overview")
assert response.status_code == 200
```

### Performance Optimization

1. **Database Indexing**:
```sql
CREATE INDEX idx_predictions_timestamp ON predictions(timestamp);
CREATE INDEX idx_metrics_timestamp_type ON performance_metrics(timestamp, metric_type);
```

2. **Data Retention**:
```python
# Implement automatic cleanup
def cleanup_old_data(days_to_keep=365):
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    # Delete old records
```

3. **Caching**:
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_analytics(cache_key: str):
    # Cached analytics computation
    pass
```

---

## 🎉 Conclusion

The Vermont Deer Prediction Analytics System provides comprehensive monitoring and analysis capabilities for the deer prediction system. With real-time performance monitoring, historical trend analysis, and an intuitive dashboard interface, it enables data-driven optimization and scientific research.

### Key Benefits

- **Performance Optimization**: Identify bottlenecks and optimization opportunities
- **Usage Analytics**: Understand user patterns and prediction accuracy
- **System Monitoring**: Proactive alerting and health monitoring
- **Configuration Impact**: Track parameter changes and their effects
- **Scientific Research**: Data collection for hunting pattern analysis

### Next Steps

1. **Production Deployment**: Configure for production environment
2. **Alert Integration**: Add email/SMS alert notifications
3. **Advanced Analytics**: Machine learning analysis of prediction patterns
4. **User Authentication**: Add security for production use
5. **Data Export**: CSV/JSON export capabilities for research

For questions or support, refer to the main system documentation or create an issue in the project repository.

---

**Version**: 1.0.0  
**Last Updated**: January 9, 2025  
**Authors**: Vermont Deer Prediction System Team
