#!/usr/bin/env python3
"""
Performance Monitor for Deer Prediction System

This module provides real-time monitoring of system performance,
including response times, resource usage, prediction accuracy,
and system health indicators.

Features:
- Real-time performance tracking
- Resource usage monitoring
- Prediction accuracy analysis
- Alert system for performance issues
- Historical trend analysis

Author: Vermont Deer Prediction System
Version: 1.0.0
"""

import psutil
import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from collections import deque
import statistics
import json

from .data_collector import get_analytics_collector, record_system_performance

logger = logging.getLogger(__name__)

@dataclass
class PerformanceAlert:
    """Performance alert notification"""
    alert_id: str
    timestamp: datetime
    severity: str  # 'info', 'warning', 'critical'
    metric_type: str
    current_value: float
    threshold_value: float
    message: str
    details: Dict[str, Any]

@dataclass
class SystemHealth:
    """Current system health status"""
    timestamp: datetime
    cpu_usage_percent: float
    memory_usage_percent: float
    disk_usage_percent: float
    network_connections: int
    response_time_avg_ms: float
    predictions_per_minute: float
    error_rate_percent: float
    overall_status: str  # 'healthy', 'warning', 'critical'

class PerformanceMonitor:
    """
    Real-time system performance monitoring
    """
    
    def __init__(self, 
                 monitoring_interval: float = 30.0,
                 history_size: int = 1000):
        """
        Initialize performance monitor
        
        Args:
            monitoring_interval: Seconds between performance checks
            history_size: Number of historical measurements to keep in memory
        """
        self.monitoring_interval = monitoring_interval
        self.history_size = history_size
        
        # Performance history (in-memory circular buffers)
        self.cpu_history = deque(maxlen=history_size)
        self.memory_history = deque(maxlen=history_size)
        self.response_time_history = deque(maxlen=history_size)
        self.prediction_count_history = deque(maxlen=history_size)
        
        # Monitoring control
        self._monitoring_active = False
        self._monitor_thread = None
        self._lock = threading.RLock()
        
        # Alert thresholds (configurable)
        self.alert_thresholds = {
            'cpu_usage_warning': 70.0,
            'cpu_usage_critical': 85.0,
            'memory_usage_warning': 75.0,
            'memory_usage_critical': 90.0,
            'response_time_warning': 2000.0,  # ms
            'response_time_critical': 5000.0,  # ms
            'error_rate_warning': 5.0,  # percent
            'error_rate_critical': 15.0  # percent
        }
        
        # Alert callbacks
        self._alert_callbacks: List[Callable[[PerformanceAlert], None]] = []
        
        # Analytics collector
        self.analytics = get_analytics_collector()
        
        logger.info("🔍 Performance Monitor initialized")
    
    def start_monitoring(self):
        """Start continuous performance monitoring"""
        if self._monitoring_active:
            logger.warning("Performance monitoring already active")
            return
        
        self._monitoring_active = True
        self._monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name="PerformanceMonitor"
        )
        self._monitor_thread.start()
        
        logger.info(f"📊 Performance monitoring started (interval: {self.monitoring_interval}s)")
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self._monitoring_active = False
        
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5.0)
        
        logger.info("🛑 Performance monitoring stopped")
    
    def add_alert_callback(self, callback: Callable[[PerformanceAlert], None]):
        """Add callback function for performance alerts"""
        self._alert_callbacks.append(callback)
        logger.info(f"📢 Alert callback added: {callback.__name__}")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        logger.info("🔄 Performance monitoring loop started")
        
        while self._monitoring_active:
            try:
                # Collect current metrics
                health = self._collect_system_metrics()
                
                # Store in history
                with self._lock:
                    self.cpu_history.append((health.timestamp, health.cpu_usage_percent))
                    self.memory_history.append((health.timestamp, health.memory_usage_percent))
                    self.response_time_history.append((health.timestamp, health.response_time_avg_ms))
                    self.prediction_count_history.append((health.timestamp, health.predictions_per_minute))
                
                # Record metrics in analytics database
                self._record_performance_metrics(health)
                
                # Check for alert conditions
                self._check_alert_conditions(health)
                
                # Sleep until next monitoring cycle
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5.0)  # Brief pause before retrying
        
        logger.info("🔄 Performance monitoring loop ended")
    
    def _collect_system_metrics(self) -> SystemHealth:
        """Collect current system performance metrics"""
        timestamp = datetime.now()
        
        # CPU and memory usage
        cpu_percent = psutil.cpu_percent(interval=1.0)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Network connections
        connections = len(psutil.net_connections())
        
        # Get prediction metrics from recent history
        response_time_avg = self._calculate_recent_avg_response_time()
        predictions_per_minute = self._calculate_predictions_per_minute()
        error_rate = self._calculate_recent_error_rate()
        
        # Determine overall health status
        overall_status = self._determine_health_status(
            cpu_percent, memory.percent, response_time_avg, error_rate
        )
        
        return SystemHealth(
            timestamp=timestamp,
            cpu_usage_percent=cpu_percent,
            memory_usage_percent=memory.percent,
            disk_usage_percent=disk.percent,
            network_connections=connections,
            response_time_avg_ms=response_time_avg,
            predictions_per_minute=predictions_per_minute,
            error_rate_percent=error_rate,
            overall_status=overall_status
        )
    
    def _calculate_recent_avg_response_time(self) -> float:
        """Calculate average response time from recent predictions"""
        try:
            # Get recent predictions from analytics
            analytics_data = self.analytics.get_prediction_analytics(days=1)
            
            if analytics_data.get('summary', {}).get('avg_response_time'):
                return float(analytics_data['summary']['avg_response_time'])
            
            # Fallback to in-memory history
            if self.response_time_history:
                recent_times = [rt for _, rt in list(self.response_time_history)[-10:]]
                return statistics.mean(recent_times) if recent_times else 0.0
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating response time: {e}")
            return 0.0
    
    def _calculate_predictions_per_minute(self) -> float:
        """Calculate predictions per minute from recent activity"""
        try:
            # Get predictions from last hour
            analytics_data = self.analytics.get_prediction_analytics(days=1)
            
            if analytics_data.get('summary', {}).get('total_predictions'):
                total_predictions = analytics_data['summary']['total_predictions']
                active_days = analytics_data['summary'].get('active_days', 1)
                
                # Convert to predictions per minute
                return (total_predictions / (active_days * 24 * 60)) if active_days > 0 else 0.0
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating predictions per minute: {e}")
            return 0.0
    
    def _calculate_recent_error_rate(self) -> float:
        """Calculate error rate from recent predictions"""
        try:
            # This would need to be implemented based on error tracking
            # For now, return a placeholder
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating error rate: {e}")
            return 0.0
    
    def _determine_health_status(self, 
                                cpu_percent: float, 
                                memory_percent: float, 
                                response_time: float, 
                                error_rate: float) -> str:
        """Determine overall system health status"""
        critical_conditions = [
            cpu_percent > self.alert_thresholds['cpu_usage_critical'],
            memory_percent > self.alert_thresholds['memory_usage_critical'],
            response_time > self.alert_thresholds['response_time_critical'],
            error_rate > self.alert_thresholds['error_rate_critical']
        ]
        
        warning_conditions = [
            cpu_percent > self.alert_thresholds['cpu_usage_warning'],
            memory_percent > self.alert_thresholds['memory_usage_warning'],
            response_time > self.alert_thresholds['response_time_warning'],
            error_rate > self.alert_thresholds['error_rate_warning']
        ]
        
        if any(critical_conditions):
            return 'critical'
        elif any(warning_conditions):
            return 'warning'
        else:
            return 'healthy'
    
    def _record_performance_metrics(self, health: SystemHealth):
        """Record performance metrics in analytics database"""
        try:
            # Record individual metrics
            record_system_performance('cpu_usage', health.cpu_usage_percent)
            record_system_performance('memory_usage', health.memory_usage_percent)
            record_system_performance('disk_usage', health.disk_usage_percent)
            record_system_performance('response_time', health.response_time_avg_ms)
            record_system_performance('predictions_per_minute', health.predictions_per_minute)
            record_system_performance('error_rate', health.error_rate_percent)
            
        except Exception as e:
            logger.error(f"Failed to record performance metrics: {e}")
    
    def _check_alert_conditions(self, health: SystemHealth):
        """Check for alert conditions and trigger notifications"""
        alerts = []
        
        # CPU usage alerts
        if health.cpu_usage_percent > self.alert_thresholds['cpu_usage_critical']:
            alerts.append(self._create_alert(
                'critical', 'cpu_usage', health.cpu_usage_percent,
                self.alert_thresholds['cpu_usage_critical'],
                f"Critical CPU usage: {health.cpu_usage_percent:.1f}%"
            ))
        elif health.cpu_usage_percent > self.alert_thresholds['cpu_usage_warning']:
            alerts.append(self._create_alert(
                'warning', 'cpu_usage', health.cpu_usage_percent,
                self.alert_thresholds['cpu_usage_warning'],
                f"High CPU usage: {health.cpu_usage_percent:.1f}%"
            ))
        
        # Memory usage alerts
        if health.memory_usage_percent > self.alert_thresholds['memory_usage_critical']:
            alerts.append(self._create_alert(
                'critical', 'memory_usage', health.memory_usage_percent,
                self.alert_thresholds['memory_usage_critical'],
                f"Critical memory usage: {health.memory_usage_percent:.1f}%"
            ))
        elif health.memory_usage_percent > self.alert_thresholds['memory_usage_warning']:
            alerts.append(self._create_alert(
                'warning', 'memory_usage', health.memory_usage_percent,
                self.alert_thresholds['memory_usage_warning'],
                f"High memory usage: {health.memory_usage_percent:.1f}%"
            ))
        
        # Response time alerts
        if health.response_time_avg_ms > self.alert_thresholds['response_time_critical']:
            alerts.append(self._create_alert(
                'critical', 'response_time', health.response_time_avg_ms,
                self.alert_thresholds['response_time_critical'],
                f"Critical response time: {health.response_time_avg_ms:.0f}ms"
            ))
        elif health.response_time_avg_ms > self.alert_thresholds['response_time_warning']:
            alerts.append(self._create_alert(
                'warning', 'response_time', health.response_time_avg_ms,
                self.alert_thresholds['response_time_warning'],
                f"Slow response time: {health.response_time_avg_ms:.0f}ms"
            ))
        
        # Error rate alerts
        if health.error_rate_percent > self.alert_thresholds['error_rate_critical']:
            alerts.append(self._create_alert(
                'critical', 'error_rate', health.error_rate_percent,
                self.alert_thresholds['error_rate_critical'],
                f"Critical error rate: {health.error_rate_percent:.1f}%"
            ))
        elif health.error_rate_percent > self.alert_thresholds['error_rate_warning']:
            alerts.append(self._create_alert(
                'warning', 'error_rate', health.error_rate_percent,
                self.alert_thresholds['error_rate_warning'],
                f"High error rate: {health.error_rate_percent:.1f}%"
            ))
        
        # Trigger alert callbacks
        for alert in alerts:
            self._trigger_alert(alert)
    
    def _create_alert(self, severity: str, metric_type: str, 
                     current_value: float, threshold_value: float, 
                     message: str) -> PerformanceAlert:
        """Create a performance alert"""
        return PerformanceAlert(
            alert_id=f"{metric_type}_{severity}_{int(time.time())}",
            timestamp=datetime.now(),
            severity=severity,
            metric_type=metric_type,
            current_value=current_value,
            threshold_value=threshold_value,
            message=message,
            details={}
        )
    
    def _trigger_alert(self, alert: PerformanceAlert):
        """Trigger alert notifications"""
        logger.warning(f"🚨 Performance Alert [{alert.severity.upper()}]: {alert.message}")
        
        # Call registered callbacks
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback {callback.__name__}: {e}")
    
    def get_current_health(self) -> SystemHealth:
        """Get current system health snapshot"""
        return self._collect_system_metrics()
    
    def get_performance_history(self, hours: int = 24) -> Dict[str, List[tuple]]:
        """Get performance history for specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self._lock:
            # Filter history by time period
            cpu_filtered = [(t, v) for t, v in self.cpu_history if t >= cutoff_time]
            memory_filtered = [(t, v) for t, v in self.memory_history if t >= cutoff_time]
            response_filtered = [(t, v) for t, v in self.response_time_history if t >= cutoff_time]
            prediction_filtered = [(t, v) for t, v in self.prediction_count_history if t >= cutoff_time]
        
        return {
            'cpu_usage': cpu_filtered,
            'memory_usage': memory_filtered,
            'response_time': response_filtered,
            'predictions_per_minute': prediction_filtered
        }
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary statistics"""
        history = self.get_performance_history(hours)
        
        summary = {}
        
        for metric_name, data_points in history.items():
            if data_points:
                values = [v for _, v in data_points]
                summary[metric_name] = {
                    'current': values[-1] if values else 0,
                    'average': statistics.mean(values),
                    'minimum': min(values),
                    'maximum': max(values),
                    'count': len(values)
                }
            else:
                summary[metric_name] = {
                    'current': 0, 'average': 0, 'minimum': 0, 'maximum': 0, 'count': 0
                }
        
        return summary

# Global performance monitor instance
_monitor_instance: Optional[PerformanceMonitor] = None

def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance (singleton pattern)"""
    global _monitor_instance
    
    if _monitor_instance is None:
        _monitor_instance = PerformanceMonitor()
    
    return _monitor_instance

def start_performance_monitoring():
    """Start global performance monitoring"""
    monitor = get_performance_monitor()
    monitor.start_monitoring()

def stop_performance_monitoring():
    """Stop global performance monitoring"""
    monitor = get_performance_monitor()
    monitor.stop_monitoring()
