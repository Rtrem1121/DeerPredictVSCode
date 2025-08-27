#!/usr/bin/env python3
"""
Analytics Module Initialization

This module initializes the analytics system components and provides
convenient imports for the deer prediction analytics functionality.
"""

from .data_collector import (
    AnalyticsCollector,
    PredictionRecord, 
    PerformanceMetric,
    ConfigurationChange,
    get_analytics_collector,
    record_prediction_analytics,
    record_system_performance
)

from .performance_monitor import (
    PerformanceMonitor,
    PerformanceAlert,
    SystemHealth,
    get_performance_monitor,
    start_performance_monitoring,
    stop_performance_monitoring
)

__version__ = "1.0.0"
__author__ = "Vermont Deer Prediction System"

# Analytics module components
__all__ = [
    # Data Collection
    "AnalyticsCollector",
    "PredictionRecord",
    "PerformanceMetric", 
    "ConfigurationChange",
    "get_analytics_collector",
    "record_prediction_analytics",
    "record_system_performance",
    
    # Performance Monitoring
    "PerformanceMonitor",
    "PerformanceAlert",
    "SystemHealth", 
    "get_performance_monitor",
    "start_performance_monitoring",
    "stop_performance_monitoring"
]
