import time
import functools
import hashlib
import json
from typing import Any, Callable, Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Simple in-memory cache for demonstration
_cache: Dict[str, Dict[str, Any]] = {}

def performance_monitor(func: Callable) -> Callable:
    """Decorator to monitor function performance"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} executed in {execution_time:.3f} seconds")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.3f} seconds: {str(e)}")
            raise
    return wrapper

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
