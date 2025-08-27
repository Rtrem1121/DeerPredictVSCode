"""
Prediction caching system to dramatically speed up repeated predictions.
"""
import hashlib
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class PredictionCache:
    """Cache for expensive prediction calculations with TTL"""
    
    def __init__(self, cache_dir: str = "prediction_cache", ttl_hours: int = 6):
        self.cache_dir = cache_dir
        self.ttl_seconds = ttl_hours * 3600
        os.makedirs(cache_dir, exist_ok=True)
        
    def _get_cache_key(self, lat: float, lon: float, season: str, hour: int) -> str:
        """Generate cache key for prediction parameters"""
        # Round coordinates to reduce cache misses for nearby locations
        lat_rounded = round(lat, 4)  # ~11 meter precision
        lon_rounded = round(lon, 4)
        return f"{lat_rounded}_{lon_rounded}_{season}_{hour}"
    
    def _get_cache_path(self, cache_key: str) -> str:
        """Get file path for cache key"""
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    def get(self, lat: float, lon: float, season: str, hour: int) -> Optional[Dict[str, Any]]:
        """Retrieve cached prediction if available and fresh"""
        try:
            cache_key = self._get_cache_key(lat, lon, season, hour)
            cache_path = self._get_cache_path(cache_key)
            
            if not os.path.exists(cache_path):
                return None
                
            # Check if cache is still fresh
            file_age = time.time() - os.path.getmtime(cache_path)
            if file_age > self.ttl_seconds:
                os.remove(cache_path)
                logger.info(f"Removed expired cache for {cache_key}")
                return None
                
            with open(cache_path, 'r') as f:
                cached_data = json.load(f)
                
            logger.info(f"Using cached prediction for {cache_key}")
            return cached_data
            
        except Exception as e:
            logger.warning(f"Failed to read cache: {e}")
            return None
    
    def set(self, lat: float, lon: float, season: str, hour: int, prediction_data: Dict[str, Any]):
        """Store prediction in cache"""
        try:
            cache_key = self._get_cache_key(lat, lon, season, hour)
            cache_path = self._get_cache_path(cache_key)
            
            # Add timestamp to cached data
            cached_data = {
                **prediction_data,
                'cached_at': datetime.now().isoformat(),
                'cache_key': cache_key
            }
            
            with open(cache_path, 'w') as f:
                json.dump(cached_data, f, indent=2, default=str)
                
            logger.info(f"Cached prediction for {cache_key}")
            
        except Exception as e:
            logger.warning(f"Failed to write cache: {e}")
    
    def clear_expired(self):
        """Remove all expired cache files"""
        try:
            current_time = time.time()
            removed_count = 0
            
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.cache_dir, filename)
                    file_age = current_time - os.path.getmtime(filepath)
                    if file_age > self.ttl_seconds:
                        os.remove(filepath)
                        removed_count += 1
                        
            if removed_count > 0:
                logger.info(f"Removed {removed_count} expired cache files")
                
        except Exception as e:
            logger.warning(f"Failed to clear expired cache: {e}")

# Global cache instance
_prediction_cache = PredictionCache()

def get_prediction_cache() -> PredictionCache:
    """Get the global prediction cache instance"""
    return _prediction_cache
