#!/usr/bin/env python3
"""
Redis Cache Service

Provides async Redis caching functionality with connection pooling,
serialization, and cache management.

Author: System Refactoring - Phase 2
Version: 2.0.0
"""

import logging
import asyncio
import json
import pickle
from typing import Any, Optional, Union, Dict, List
from datetime import datetime, timedelta
from dataclasses import dataclass

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    try:
        import redis
        REDIS_AVAILABLE = True
    except ImportError:
        REDIS_AVAILABLE = False

from backend.services.base_service import BaseService, Result, AppError, ErrorCode

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry metadata"""
    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime]
    size_bytes: int
    hit_count: int


class RedisCacheService(BaseService):
    """
    Async Redis cache service with connection pooling and advanced features
    
    Features:
    - Connection pooling for performance
    - JSON and pickle serialization
    - TTL management
    - Cache statistics
    - Bulk operations
    - Health monitoring
    """
    
    def __init__(self, 
                 redis_url: str = "redis://localhost:6379/0",
                 max_connections: int = 50,
                 default_ttl_seconds: int = 3600):
        super().__init__()
        self.redis_url = redis_url
        self.max_connections = max_connections
        self.default_ttl_seconds = default_ttl_seconds
        self._pool: Optional[redis.ConnectionPool] = None
        self._client: Optional[redis.Redis] = None
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0
        }
        
        if not REDIS_AVAILABLE:
            self.logger.warning("Redis not available - caching functionality limited")
    
    async def _get_client(self) -> redis.Redis:
        """Get or create Redis client with connection pooling"""
        if not REDIS_AVAILABLE:
            raise RuntimeError("Redis not installed - cannot create cache client")
        
        if self._client is None:
            # Create connection pool
            self._pool = redis.ConnectionPool.from_url(
                self.redis_url,
                max_connections=self.max_connections,
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30
            )
            
            # Create Redis client
            self._client = redis.Redis(connection_pool=self._pool)
            
            self.logger.debug("Created Redis client with connection pooling")
        
        return self._client
    
    async def get(self, key: str, default: Any = None) -> Result[Any]:
        """
        Get value from cache with deserialization
        
        Args:
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Result containing cached value or default
        """
        try:
            self.log_operation_start("cache_get", key=key)
            
            if not REDIS_AVAILABLE:
                return Result.success(default)
            
            client = await self._get_client()
            
            # Get raw value from Redis
            raw_value = await client.get(key)
            
            if raw_value is None:
                self._stats["misses"] += 1
                self.logger.debug(f"Cache miss for key: {key}")
                return Result.success(default)
            
            # Deserialize value
            try:
                # Try JSON first (more common)
                if raw_value.startswith(b'{"__type__":"json",'):
                    json_data = json.loads(raw_value.decode('utf-8'))
                    value = json_data.get("data")
                elif raw_value.startswith(b'{"__type__":"pickle",'):
                    pickle_data = json.loads(raw_value.decode('utf-8'))
                    import base64
                    value = pickle.loads(base64.b64decode(pickle_data["data"]))
                else:
                    # Plain string
                    value = raw_value.decode('utf-8')
                
                self._stats["hits"] += 1
                self.log_operation_success("cache_get", key=key, hit=True)
                return Result.success(value)
                
            except (json.JSONDecodeError, pickle.PickleError, UnicodeDecodeError) as e:
                self.logger.warning(f"Failed to deserialize cached value for key {key}: {e}")
                # Delete corrupted entry
                await client.delete(key)
                self._stats["misses"] += 1
                return Result.success(default)
            
        except Exception as e:
            self._stats["errors"] += 1
            error = self.handle_unexpected_error("cache_get", e, key=key)
            return Result.failure(error)
    
    async def set(self, key: str, value: Any, 
                  ttl_seconds: Optional[int] = None) -> Result[bool]:
        """
        Set value in cache with serialization and TTL
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds (None for default)
            
        Returns:
            Result containing success status
        """
        try:
            self.log_operation_start("cache_set", key=key, ttl_seconds=ttl_seconds)
            
            if not REDIS_AVAILABLE:
                return Result.success(True)  # Silently succeed when Redis unavailable
            
            client = await self._get_client()
            
            # Serialize value
            serialized_value = self._serialize_value(value)
            
            # Set TTL
            ttl = ttl_seconds or self.default_ttl_seconds
            
            # Store in Redis
            success = await client.setex(key, ttl, serialized_value)
            
            if success:
                self._stats["sets"] += 1
                self.log_operation_success("cache_set", key=key, ttl_seconds=ttl)
                return Result.success(True)
            else:
                return Result.failure(AppError(
                    ErrorCode.CACHE_OPERATION_FAILED,
                    f"Failed to set cache key: {key}",
                    {"key": key, "ttl_seconds": ttl}
                ))
            
        except Exception as e:
            self._stats["errors"] += 1
            error = self.handle_unexpected_error("cache_set", e, key=key)
            return Result.failure(error)
    
    async def delete(self, key: str) -> Result[bool]:
        """
        Delete key from cache
        
        Args:
            key: Cache key to delete
            
        Returns:
            Result containing success status
        """
        try:
            self.log_operation_start("cache_delete", key=key)
            
            if not REDIS_AVAILABLE:
                return Result.success(True)
            
            client = await self._get_client()
            
            # Delete from Redis
            deleted_count = await client.delete(key)
            
            self._stats["deletes"] += 1
            self.log_operation_success("cache_delete", key=key, deleted=deleted_count > 0)
            return Result.success(deleted_count > 0)
            
        except Exception as e:
            self._stats["errors"] += 1
            error = self.handle_unexpected_error("cache_delete", e, key=key)
            return Result.failure(error)
    
    async def exists(self, key: str) -> Result[bool]:
        """Check if key exists in cache"""
        try:
            if not REDIS_AVAILABLE:
                return Result.success(False)
            
            client = await self._get_client()
            exists = await client.exists(key)
            return Result.success(bool(exists))
            
        except Exception as e:
            error = self.handle_unexpected_error("cache_exists", e, key=key)
            return Result.failure(error)
    
    async def get_ttl(self, key: str) -> Result[Optional[int]]:
        """Get time to live for a key in seconds"""
        try:
            if not REDIS_AVAILABLE:
                return Result.success(None)
            
            client = await self._get_client()
            ttl = await client.ttl(key)
            
            if ttl == -1:  # Key exists but no expiration
                return Result.success(None)
            elif ttl == -2:  # Key does not exist
                return Result.success(None)
            else:
                return Result.success(ttl)
            
        except Exception as e:
            error = self.handle_unexpected_error("cache_get_ttl", e, key=key)
            return Result.failure(error)
    
    async def bulk_get(self, keys: List[str]) -> Result[Dict[str, Any]]:
        """Get multiple values from cache"""
        try:
            self.log_operation_start("cache_bulk_get", key_count=len(keys))
            
            if not REDIS_AVAILABLE:
                return Result.success({})
            
            client = await self._get_client()
            
            # Use mget for efficiency
            raw_values = await client.mget(keys)
            
            result = {}
            for key, raw_value in zip(keys, raw_values):
                if raw_value is not None:
                    try:
                        # Deserialize value (simplified version)
                        if raw_value.startswith(b'{"__type__":"json",'):
                            json_data = json.loads(raw_value.decode('utf-8'))
                            result[key] = json_data.get("data")
                        else:
                            result[key] = raw_value.decode('utf-8')
                    except Exception as e:
                        self.logger.warning(f"Failed to deserialize bulk value for key {key}: {e}")
                        continue
            
            self.log_operation_success("cache_bulk_get", 
                                     key_count=len(keys), 
                                     found_count=len(result))
            return Result.success(result)
            
        except Exception as e:
            error = self.handle_unexpected_error("cache_bulk_get", e, key_count=len(keys))
            return Result.failure(error)
    
    async def clear_pattern(self, pattern: str) -> Result[int]:
        """Delete all keys matching a pattern"""
        try:
            self.log_operation_start("cache_clear_pattern", pattern=pattern)
            
            if not REDIS_AVAILABLE:
                return Result.success(0)
            
            client = await self._get_client()
            
            # Find matching keys
            keys = await client.keys(pattern)
            
            if keys:
                # Delete in batches
                deleted_count = await client.delete(*keys)
                self._stats["deletes"] += deleted_count
            else:
                deleted_count = 0
            
            self.log_operation_success("cache_clear_pattern", 
                                     pattern=pattern, 
                                     deleted_count=deleted_count)
            return Result.success(deleted_count)
            
        except Exception as e:
            error = self.handle_unexpected_error("cache_clear_pattern", e, pattern=pattern)
            return Result.failure(error)
    
    def _serialize_value(self, value: Any) -> bytes:
        """Serialize value for storage"""
        try:
            # Try JSON serialization first (more efficient)
            json_str = json.dumps(value)
            return json.dumps({
                "__type__": "json",
                "data": value
            }).encode('utf-8')
        except (TypeError, ValueError):
            # Fall back to pickle for complex objects
            import base64
            pickle_data = base64.b64encode(pickle.dumps(value)).decode('utf-8')
            return json.dumps({
                "__type__": "pickle", 
                "data": pickle_data
            }).encode('utf-8')
    
    async def get_stats(self) -> Result[Dict[str, Any]]:
        """Get cache statistics"""
        try:
            total_operations = sum(self._stats.values())
            hit_ratio = (self._stats["hits"] / (self._stats["hits"] + self._stats["misses"])) if (self._stats["hits"] + self._stats["misses"]) > 0 else 0
            
            stats = {
                **self._stats,
                "total_operations": total_operations,
                "hit_ratio": hit_ratio,
                "redis_available": REDIS_AVAILABLE
            }
            
            if REDIS_AVAILABLE and self._client:
                # Get Redis info
                client = await self._get_client()
                redis_info = await client.info()
                stats.update({
                    "redis_memory_usage": redis_info.get("used_memory_human", "unknown"),
                    "redis_connected_clients": redis_info.get("connected_clients", 0),
                    "redis_keyspace_hits": redis_info.get("keyspace_hits", 0),
                    "redis_keyspace_misses": redis_info.get("keyspace_misses", 0)
                })
            
            return Result.success(stats)
            
        except Exception as e:
            error = self.handle_unexpected_error("cache_get_stats", e)
            return Result.failure(error)
    
    async def health_check(self) -> Result[Dict[str, Any]]:
        """Check cache service health"""
        try:
            health_data = {
                "service": "RedisCacheService",
                "status": "healthy",
                "redis_available": REDIS_AVAILABLE,
                "stats": self._stats
            }
            
            if REDIS_AVAILABLE and self._client:
                try:
                    # Test Redis connection
                    client = await self._get_client()
                    await client.ping()
                    health_data["redis_connection"] = "connected"
                except Exception as e:
                    health_data["redis_connection"] = f"error: {str(e)}"
                    health_data["status"] = "degraded"
            
            return Result.success(health_data)
            
        except Exception as e:
            error = self.handle_unexpected_error("health_check", e)
            return Result.failure(error)
    
    async def shutdown(self) -> None:
        """Gracefully shutdown cache service"""
        try:
            if self._client:
                await self._client.close()
                self.logger.debug("Redis client closed")
            
            if self._pool:
                await self._pool.disconnect()
                self.logger.debug("Redis connection pool closed")
            
        except Exception as e:
            self.logger.error(f"Error during cache service shutdown: {e}")


# Factory function for dependency injection
def create_redis_cache_service() -> RedisCacheService:
    """Create a new RedisCacheService instance"""
    return RedisCacheService()
