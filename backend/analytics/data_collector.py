#!/usr/bin/env python3
"""
Analytics Data Collection System

This module provides comprehensive analytics collection for the deer prediction system.
It tracks predictions, performance metrics, configuration changes, and user interactions
to enable data-driven optimization and scientific research.

Key Features:
- Prediction accuracy tracking
- Performance metrics collection
- Configuration parameter impact analysis
- User interaction analytics
- Real-time system monitoring

Author: Vermont Deer Prediction System
Version: 1.0.0
"""

import sqlite3
import json
import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict, field
from pathlib import Path
import numpy as np
from contextlib import contextmanager

# Import configuration management
import sys
from pathlib import Path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))
from config_manager import get_config

logger = logging.getLogger(__name__)

@dataclass
class PredictionRecord:
    """Record of a prediction request and its details"""
    prediction_id: str
    timestamp: datetime
    latitude: float
    longitude: float
    season: str
    weather_conditions: List[str]
    time_of_day: str
    
    # Prediction results
    stand_rating: float
    confidence_score: float
    mature_buck_score: Optional[float] = None
    
    # Performance metrics
    response_time_ms: float = 0.0
    processing_time_ms: float = 0.0
    
    # Configuration context
    config_version: str = ""
    config_environment: str = ""
    
    # User feedback (if available)
    actual_success: Optional[bool] = None
    user_feedback_score: Optional[int] = None
    notes: str = ""

@dataclass
class PerformanceMetric:
    """System performance metric record"""
    metric_id: str
    timestamp: datetime
    metric_type: str  # 'response_time', 'cpu_usage', 'memory_usage', 'prediction_count'
    value: float
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ConfigurationChange:
    """Configuration parameter change record"""
    change_id: str
    timestamp: datetime
    parameter_path: str
    old_value: Any
    new_value: Any
    changed_by: str = "system"
    reason: str = ""

class AnalyticsCollector:
    """
    Centralized analytics data collection system
    """
    
    def __init__(self, db_path: str = None):
        """Initialize analytics collector with database"""
        self.db_path = db_path or self._get_default_db_path()
        self.config = get_config()
        self._lock = threading.RLock()
        
        # Initialize database
        self._init_database()
        
        logger.info(f"📊 Analytics Collector initialized with database: {self.db_path}")
    
    def _get_default_db_path(self) -> str:
        """Get default analytics database path"""
        app_dir = Path(__file__).parent.parent.parent
        analytics_dir = app_dir / "analytics_data"
        analytics_dir.mkdir(exist_ok=True)
        return str(analytics_dir / "deer_prediction_analytics.db")
    
    def _init_database(self):
        """Initialize analytics database with required tables"""
        with self._get_db_connection() as conn:
            # Predictions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    prediction_id TEXT PRIMARY KEY,
                    timestamp DATETIME,
                    latitude REAL,
                    longitude REAL,
                    season TEXT,
                    weather_conditions TEXT,
                    time_of_day TEXT,
                    stand_rating REAL,
                    confidence_score REAL,
                    mature_buck_score REAL,
                    response_time_ms REAL,
                    processing_time_ms REAL,
                    config_version TEXT,
                    config_environment TEXT,
                    actual_success INTEGER,
                    user_feedback_score INTEGER,
                    notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Performance metrics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    metric_id TEXT PRIMARY KEY,
                    timestamp DATETIME,
                    metric_type TEXT,
                    value REAL,
                    details TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Configuration changes table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS configuration_changes (
                    change_id TEXT PRIMARY KEY,
                    timestamp DATETIME,
                    parameter_path TEXT,
                    old_value TEXT,
                    new_value TEXT,
                    changed_by TEXT,
                    reason TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Analytics summary table for quick access
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analytics_summary (
                    summary_date DATE PRIMARY KEY,
                    total_predictions INTEGER,
                    avg_confidence_score REAL,
                    avg_response_time_ms REAL,
                    success_rate REAL,
                    unique_users INTEGER,
                    config_changes INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            logger.info("✅ Analytics database initialized successfully")
    
    @contextmanager
    def _get_db_connection(self):
        """Get database connection with proper error handling"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def record_prediction(self, prediction_record: PredictionRecord):
        """Record a prediction request and its results"""
        with self._lock:
            try:
                with self._get_db_connection() as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO predictions (
                            prediction_id, timestamp, latitude, longitude, season,
                            weather_conditions, time_of_day, stand_rating, confidence_score,
                            mature_buck_score, response_time_ms, processing_time_ms,
                            config_version, config_environment, actual_success,
                            user_feedback_score, notes
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        prediction_record.prediction_id,
                        prediction_record.timestamp,
                        prediction_record.latitude,
                        prediction_record.longitude,
                        prediction_record.season,
                        json.dumps(prediction_record.weather_conditions),
                        prediction_record.time_of_day,
                        prediction_record.stand_rating,
                        prediction_record.confidence_score,
                        prediction_record.mature_buck_score,
                        prediction_record.response_time_ms,
                        prediction_record.processing_time_ms,
                        prediction_record.config_version,
                        prediction_record.config_environment,
                        prediction_record.actual_success,
                        prediction_record.user_feedback_score,
                        prediction_record.notes
                    ))
                    conn.commit()
                    
                logger.debug(f"📊 Recorded prediction: {prediction_record.prediction_id}")
                
            except Exception as e:
                logger.error(f"Failed to record prediction: {e}")
    
    def record_performance_metric(self, metric: PerformanceMetric):
        """Record a system performance metric"""
        with self._lock:
            try:
                with self._get_db_connection() as conn:
                    conn.execute("""
                        INSERT INTO performance_metrics (
                            metric_id, timestamp, metric_type, value, details
                        ) VALUES (?, ?, ?, ?, ?)
                    """, (
                        metric.metric_id,
                        metric.timestamp,
                        metric.metric_type,
                        metric.value,
                        json.dumps(metric.details)
                    ))
                    conn.commit()
                    
                logger.debug(f"📈 Recorded performance metric: {metric.metric_type} = {metric.value}")
                
            except Exception as e:
                logger.error(f"Failed to record performance metric: {e}")
    
    def record_config_change(self, change: ConfigurationChange):
        """Record a configuration parameter change"""
        with self._lock:
            try:
                with self._get_db_connection() as conn:
                    conn.execute("""
                        INSERT INTO configuration_changes (
                            change_id, timestamp, parameter_path, old_value,
                            new_value, changed_by, reason
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        change.change_id,
                        change.timestamp,
                        change.parameter_path,
                        json.dumps(change.old_value),
                        json.dumps(change.new_value),
                        change.changed_by,
                        change.reason
                    ))
                    conn.commit()
                    
                logger.info(f"🔧 Recorded config change: {change.parameter_path}")
                
            except Exception as e:
                logger.error(f"Failed to record configuration change: {e}")
    
    def get_prediction_analytics(self, 
                                days: int = 7, 
                                season: str = None,
                                min_confidence: float = None) -> Dict[str, Any]:
        """Get prediction analytics for specified time period"""
        try:
            with self._get_db_connection() as conn:
                # Base query
                where_clauses = ["timestamp >= datetime('now', '-{} days')".format(days)]
                params = []
                
                if season:
                    where_clauses.append("season = ?")
                    params.append(season)
                
                if min_confidence is not None:
                    where_clauses.append("confidence_score >= ?")
                    params.append(min_confidence)
                
                where_clause = " AND ".join(where_clauses)
                
                # Get summary statistics
                cursor = conn.execute(f"""
                    SELECT 
                        COUNT(*) as total_predictions,
                        AVG(confidence_score) as avg_confidence,
                        AVG(stand_rating) as avg_rating,
                        AVG(response_time_ms) as avg_response_time,
                        MIN(timestamp) as first_prediction,
                        MAX(timestamp) as last_prediction,
                        COUNT(DISTINCT DATE(timestamp)) as active_days
                    FROM predictions 
                    WHERE {where_clause}
                """, params)
                
                summary = dict(cursor.fetchone())
                
                # Get daily prediction counts
                cursor = conn.execute(f"""
                    SELECT 
                        DATE(timestamp) as prediction_date,
                        COUNT(*) as count,
                        AVG(confidence_score) as avg_confidence
                    FROM predictions 
                    WHERE {where_clause}
                    GROUP BY DATE(timestamp)
                    ORDER BY prediction_date
                """, params)
                
                daily_stats = [dict(row) for row in cursor.fetchall()]
                
                # Get confidence distribution
                cursor = conn.execute(f"""
                    SELECT 
                        CASE 
                            WHEN confidence_score < 30 THEN 'Low (0-30)'
                            WHEN confidence_score < 60 THEN 'Medium (30-60)'
                            WHEN confidence_score < 80 THEN 'High (60-80)'
                            ELSE 'Very High (80+)'
                        END as confidence_range,
                        COUNT(*) as count
                    FROM predictions 
                    WHERE {where_clause}
                    GROUP BY confidence_range
                """, params)
                
                confidence_distribution = [dict(row) for row in cursor.fetchall()]
                
                return {
                    "summary": summary,
                    "daily_stats": daily_stats,
                    "confidence_distribution": confidence_distribution,
                    "query_period_days": days,
                    "filters": {
                        "season": season,
                        "min_confidence": min_confidence
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to get prediction analytics: {e}")
            return {"error": str(e)}
    
    def get_performance_analytics(self, hours: int = 24) -> Dict[str, Any]:
        """Get system performance analytics"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.execute("""
                    SELECT 
                        metric_type,
                        AVG(value) as avg_value,
                        MIN(value) as min_value,
                        MAX(value) as max_value,
                        COUNT(*) as measurement_count
                    FROM performance_metrics 
                    WHERE timestamp >= datetime('now', '-{} hours')
                    GROUP BY metric_type
                """.format(hours))
                
                metrics_summary = [dict(row) for row in cursor.fetchall()]
                
                # Get recent performance trends
                cursor = conn.execute("""
                    SELECT 
                        datetime(timestamp) as measurement_time,
                        metric_type,
                        value
                    FROM performance_metrics 
                    WHERE timestamp >= datetime('now', '-{} hours')
                    ORDER BY timestamp DESC
                    LIMIT 100
                """.format(hours))
                
                recent_metrics = [dict(row) for row in cursor.fetchall()]
                
                return {
                    "summary": metrics_summary,
                    "recent_trends": recent_metrics,
                    "query_period_hours": hours
                }
                
        except Exception as e:
            logger.error(f"Failed to get performance analytics: {e}")
            return {"error": str(e)}
    
    def update_daily_summary(self, target_date: datetime = None):
        """Update daily analytics summary for efficient dashboard queries"""
        if target_date is None:
            target_date = datetime.now()
        
        date_str = target_date.strftime('%Y-%m-%d')
        
        try:
            with self._get_db_connection() as conn:
                # Calculate daily summary statistics
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total_predictions,
                        AVG(confidence_score) as avg_confidence,
                        AVG(response_time_ms) as avg_response_time,
                        AVG(CASE WHEN actual_success = 1 THEN 1.0 ELSE 0.0 END) as success_rate,
                        COUNT(DISTINCT prediction_id) as unique_predictions
                    FROM predictions 
                    WHERE DATE(timestamp) = ?
                """, (date_str,))
                
                summary = cursor.fetchone()
                
                if summary and summary[0] > 0:  # If there are predictions for this date
                    # Get configuration changes count
                    cursor = conn.execute("""
                        SELECT COUNT(*) as config_changes
                        FROM configuration_changes 
                        WHERE DATE(timestamp) = ?
                    """, (date_str,))
                    
                    config_changes = cursor.fetchone()[0]
                    
                    # Insert or update summary
                    conn.execute("""
                        INSERT OR REPLACE INTO analytics_summary (
                            summary_date, total_predictions, avg_confidence_score,
                            avg_response_time_ms, success_rate, unique_users, config_changes
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        date_str,
                        summary[0],  # total_predictions
                        summary[1],  # avg_confidence
                        summary[2],  # avg_response_time
                        summary[3] or 0.0,  # success_rate
                        summary[4],  # unique_predictions (as proxy for users)
                        config_changes
                    ))
                    
                    conn.commit()
                    logger.info(f"📊 Updated daily summary for {date_str}")
                
        except Exception as e:
            logger.error(f"Failed to update daily summary: {e}")

# Global analytics collector instance
_analytics_instance: Optional[AnalyticsCollector] = None

def get_analytics_collector() -> AnalyticsCollector:
    """Get global analytics collector instance (singleton pattern)"""
    global _analytics_instance
    
    if _analytics_instance is None:
        _analytics_instance = AnalyticsCollector()
    
    return _analytics_instance

def record_prediction_analytics(prediction_id: str,
                               request_data: Dict[str, Any],
                               response_data: Dict[str, Any],
                               performance_data: Dict[str, Any]):
    """Convenience function to record prediction analytics"""
    collector = get_analytics_collector()
    
    # Create prediction record
    record = PredictionRecord(
        prediction_id=prediction_id,
        timestamp=datetime.now(),
        latitude=request_data.get('lat', 0.0),
        longitude=request_data.get('lon', 0.0),
        season=request_data.get('season', ''),
        weather_conditions=request_data.get('weather_conditions', []),
        time_of_day=request_data.get('time_of_day', ''),
        stand_rating=response_data.get('stand_rating', 0.0),
        confidence_score=response_data.get('confidence_score', 0.0),
        mature_buck_score=response_data.get('mature_buck_score'),
        response_time_ms=performance_data.get('response_time_ms', 0.0),
        processing_time_ms=performance_data.get('processing_time_ms', 0.0),
        config_version=get_config().metadata.version,
        config_environment=get_config().metadata.environment
    )
    
    collector.record_prediction(record)

def record_system_performance(metric_type: str, value: float, details: Dict[str, Any] = None):
    """Convenience function to record system performance metrics"""
    collector = get_analytics_collector()
    
    metric = PerformanceMetric(
        metric_id=f"{metric_type}_{int(time.time() * 1000)}",
        timestamp=datetime.now(),
        metric_type=metric_type,
        value=value,
        details=details or {}
    )
    
    collector.record_performance_metric(metric)
