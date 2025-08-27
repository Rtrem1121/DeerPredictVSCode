"""
Performance monitoring and optimization utilities.
Provides decorators and utilities for monitoring application performance.
"""
import time
import logging
import functools
import asyncio
from typing import Dict, Any, Callable, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
import threading
import hashlib
import json

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Performance metric data"""
    function_name: str
    execution_time: float
    timestamp: datetime
    args_count: int
    kwargs_count: int
    success: bool
    error_message: Optional[str] = None


@dataclass 
class PerformanceStats:
    """Aggregated performance statistics"""
    function_name: str
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    avg_time: float = 0.0
    last_called: Optional[datetime] = None
    error_rate: float = 0.0


class PerformanceMonitor:
    """Thread-safe performance monitoring system"""
    
    def __init__(self, max_metrics: int = 10000):
        self.max_metrics = max_metrics
        self.metrics: deque = deque(maxlen=max_metrics)
        self.stats: Dict[str, PerformanceStats] = defaultdict(
            lambda: PerformanceStats("")
        )
        self._lock = threading.RLock()
    
    def record_metric(self, metric: PerformanceMetric) -> None:
        """
        Record a performance metric.
        
        Args:
            metric: Performance metric to record
        """
        with self._lock:
            self.metrics.append(metric)
            self._update_stats(metric)
    
    def _update_stats(self, metric: PerformanceMetric) -> None:
        """Update aggregated statistics"""
        stats = self.stats[metric.function_name]
        stats.function_name = metric.function_name
        stats.total_calls += 1
        stats.last_called = metric.timestamp
        
        if metric.success:
            stats.successful_calls += 1
            stats.total_time += metric.execution_time
            stats.min_time = min(stats.min_time, metric.execution_time)
            stats.max_time = max(stats.max_time, metric.execution_time)
            stats.avg_time = stats.total_time / stats.successful_calls
        else:
            stats.failed_calls += 1
        
        stats.error_rate = (stats.failed_calls / stats.total_calls) * 100
    
    def get_stats(self, function_name: Optional[str] = None) -> Dict[str, PerformanceStats]:
        """
        Get performance statistics.
        
        Args:
            function_name: Specific function name, or None for all
            
        Returns:
            Dict[str, PerformanceStats]: Performance statistics
        """
        with self._lock:
            if function_name:
                return {function_name: self.stats.get(function_name, PerformanceStats(function_name))}
            return dict(self.stats)
    
    def get_slow_functions(self, threshold_seconds: float = 1.0) -> List[PerformanceStats]:
        """
        Get functions that exceed execution time threshold.
        
        Args:
            threshold_seconds: Execution time threshold
            
        Returns:
            List[PerformanceStats]: Slow functions
        """
        with self._lock:
            return [
                stats for stats in self.stats.values()
                if stats.avg_time > threshold_seconds
            ]
    
    def get_error_prone_functions(self, error_rate_threshold: float = 5.0) -> List[PerformanceStats]:
        """
        Get functions with high error rates.
        
        Args:
            error_rate_threshold: Error rate percentage threshold
            
        Returns:
            List[PerformanceStats]: Error-prone functions
        """
        with self._lock:
            return [
                stats for stats in self.stats.values()
                if stats.error_rate > error_rate_threshold and stats.total_calls > 10
            ]


# Global performance monitor instance
_performance_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance"""
    return _performance_monitor


def performance_monitor(
    log_slow_calls: bool = True,
    slow_threshold: float = 1.0,
    log_errors: bool = True
):
    """
    Decorator to monitor function performance.
    
    Args:
        log_slow_calls: Whether to log slow function calls
        slow_threshold: Threshold in seconds for slow calls
        log_errors: Whether to log function errors
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            error_message = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error_message = str(e)
                if log_errors:
                    logger.error(f"Error in {func.__name__}: {error_message}")
                raise
            finally:
                execution_time = time.time() - start_time
                
                # Record metric
                metric = PerformanceMetric(
                    function_name=func.__name__,
                    execution_time=execution_time,
                    timestamp=datetime.now(),
                    args_count=len(args),
                    kwargs_count=len(kwargs),
                    success=success,
                    error_message=error_message
                )
                _performance_monitor.record_metric(metric)
                
                # Log slow calls
                if log_slow_calls and execution_time > slow_threshold:
                    logger.warning(
                        f"Slow function call: {func.__name__} took {execution_time:.2f}s"
                    )
        
        return wrapper
    
    return decorator

def cache_result(ttl_hours: int = 24) -> Callable:
    """Decorator to cache function results"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = _create_cache_key(func.__name__, args, kwargs)
            
            # Check if result is in cache and not expired
            if cache_key in _cache:
                cache_entry = _cache[cache_key]
                if time.time() - cache_entry['timestamp'] < ttl_hours * 3600:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cache_entry['result']
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            _cache[cache_key] = {
                'result': result,
                'timestamp': time.time()
            }
            logger.debug(f"Cache miss for {func.__name__}, result cached")
            return result
        return wrapper
    return decorator

def _create_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """Create a unique cache key from function name and arguments"""
    # Convert arguments to string representation
    args_str = str(args)
    kwargs_str = json.dumps(kwargs, sort_keys=True, default=str)
    cache_input = f"{func_name}:{args_str}:{kwargs_str}"
    
    # Create hash to ensure consistent key length
    return hashlib.md5(cache_input.encode()).hexdigest()

def clear_cache():
    """Clear all cached results"""
    global _cache
    _cache.clear()
    logger.info("Cache cleared")

def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics"""
    total_entries = len(_cache)
    current_time = time.time()
    expired_entries = sum(
        1 for entry in _cache.values() 
        if current_time - entry['timestamp'] > 24 * 3600
    )
    
    return {
        'total_entries': total_entries,
        'expired_entries': expired_entries,
        'active_entries': total_entries - expired_entries
    }
