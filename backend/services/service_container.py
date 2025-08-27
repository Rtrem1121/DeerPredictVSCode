#!/usr/bin/env python3
"""
Dependency Injection Container

Manages service dependencies and provides dependency injection functionality
for the refactored service architecture.

Author: System Refactoring  
Version: 2.0.0
"""

import logging
from typing import TypeVar, Type, Any, Dict, Optional, Callable, List
from abc import ABC
from dataclasses import dataclass

from backend.services.base_service import BaseService, Result, AppError, ErrorCode

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ServiceContainer:
    """
    Dependency injection container for managing service instances and dependencies
    
    Features:
    - Service registration with factory functions
    - Singleton and transient lifetimes
    - Dependency resolution
    - Service health checking
    - Graceful service shutdown
    """
    
    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable] = {}
        self._singletons: Dict[Type, Any] = {}
        self._transients: set = set()
        self.logger = logging.getLogger(__name__)
    
    def register_singleton(self, service_type: Type[T], factory: Callable[[], T]) -> None:
        """Register a service as singleton (single instance per container)"""
        self._factories[service_type] = factory
        self.logger.debug(f"Registered singleton service: {service_type.__name__}")
    
    def register_transient(self, service_type: Type[T], factory: Callable[[], T]) -> None:
        """Register a service as transient (new instance per request)"""
        self._factories[service_type] = factory
        self._transients.add(service_type)
        self.logger.debug(f"Registered transient service: {service_type.__name__}")
    
    def register_instance(self, service_type: Type[T], instance: T) -> None:
        """Register a specific instance of a service"""
        self._singletons[service_type] = instance
        self.logger.debug(f"Registered service instance: {service_type.__name__}")
    
    def get(self, service_type: Type[T]) -> T:
        """Get an instance of the specified service type"""
        try:
            # Check if it's a singleton and already instantiated
            if service_type in self._singletons:
                return self._singletons[service_type]
            
            # Check if we have a factory
            if service_type not in self._factories:
                raise ValueError(f"Service not registered: {service_type.__name__}")
            
            # Create instance
            factory = self._factories[service_type]
            instance = factory()
            
            # Store if singleton
            if service_type not in self._transients:
                self._singletons[service_type] = instance
            
            self.logger.debug(f"Created service instance: {service_type.__name__}")
            return instance
            
        except Exception as e:
            self.logger.error(f"Failed to create service {service_type.__name__}: {e}")
            raise
    
    def is_registered(self, service_type: Type[T]) -> bool:
        """Check if a service type is registered"""
        return service_type in self._factories or service_type in self._singletons
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all registered services"""
        health_status = {
            "container_status": "healthy",
            "services": {},
            "total_services": len(self._singletons) + len(self._factories),
            "singleton_count": len(self._singletons),
            "factory_count": len(self._factories)
        }
        
        # Check singleton instances
        for service_type, instance in self._singletons.items():
            try:
                if hasattr(instance, 'health_check') and callable(getattr(instance, 'health_check')):
                    result = await instance.health_check()
                    health_status["services"][service_type.__name__] = {
                        "status": "healthy" if result.is_success else "unhealthy",
                        "type": "singleton",
                        "details": result.value if result.is_success else result.error.message
                    }
                else:
                    health_status["services"][service_type.__name__] = {
                        "status": "unknown",
                        "type": "singleton", 
                        "details": "No health check method available"
                    }
            except Exception as e:
                health_status["services"][service_type.__name__] = {
                    "status": "error",
                    "type": "singleton",
                    "details": f"Health check failed: {str(e)}"
                }
                health_status["container_status"] = "degraded"
        
        return health_status
    
    async def shutdown(self) -> None:
        """Gracefully shutdown all services"""
        self.logger.info("Shutting down service container...")
        
        shutdown_errors = []
        
        # Shutdown singletons that support it
        for service_type, instance in self._singletons.items():
            try:
                if hasattr(instance, 'shutdown') and callable(getattr(instance, 'shutdown')):
                    await instance.shutdown()
                    self.logger.debug(f"Shutdown service: {service_type.__name__}")
            except Exception as e:
                error_msg = f"Failed to shutdown {service_type.__name__}: {str(e)}"
                self.logger.error(error_msg)
                shutdown_errors.append(error_msg)
        
        # Clear all registrations
        self._services.clear()
        self._factories.clear() 
        self._singletons.clear()
        self._transients.clear()
        
        if shutdown_errors:
            self.logger.warning(f"Service container shutdown completed with {len(shutdown_errors)} errors")
        else:
            self.logger.info("Service container shutdown completed successfully")


# Global container instance
_container: Optional[ServiceContainer] = None


def get_container() -> ServiceContainer:
    """Get the global service container instance"""
    global _container
    if _container is None:
        _container = ServiceContainer()
        _setup_default_services()
    return _container


def _setup_default_services() -> None:
    """Setup default service registrations"""
    from backend.services.terrain_service import TerrainAnalysisService
    from backend.services.weather_service import WeatherService
    from backend.services.scouting_data_service import ScoutingDataService
    from backend.services.async_http_service import AsyncHttpService
    from backend.services.redis_cache_service import RedisCacheService
    from backend.services.async_prediction_service import AsyncPredictionService
    
    container = get_container()
    
    # Register core services as singletons
    container.register_singleton(TerrainAnalysisService, lambda: TerrainAnalysisService())
    container.register_singleton(WeatherService, lambda: WeatherService())
    container.register_singleton(ScoutingDataService, lambda: ScoutingDataService())
    
    # Register Phase 2 async services as singletons
    container.register_singleton(AsyncHttpService, lambda: AsyncHttpService())
    container.register_singleton(RedisCacheService, lambda: RedisCacheService())
    container.register_singleton(AsyncPredictionService, lambda: AsyncPredictionService())
    
    logger.info("All services registered in container (Phase 1 + Phase 2)")


def reset_container() -> None:
    """Reset the global container (useful for testing)"""
    global _container
    if _container:
        import asyncio
        asyncio.create_task(_container.shutdown())
    _container = None


# Convenience functions for common dependency injection patterns

def inject_service(service_type: Type[T]) -> T:
    """Inject a service dependency (for use in service constructors)"""
    return get_container().get(service_type)


def with_service(service_type: Type[T]) -> Callable:
    """Decorator to inject service as first parameter after self"""
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            service = get_container().get(service_type)
            return func(self, service, *args, **kwargs)
        return wrapper
    return decorator


@dataclass
class ServiceHealth:
    """Service health status information"""
    service_name: str
    status: str  # healthy, degraded, unhealthy
    details: Dict[str, Any]
    last_check: str


class ServiceRegistry:
    """
    Service registry for tracking available services and their capabilities
    """
    
    def __init__(self):
        self._service_metadata: Dict[Type, Dict[str, Any]] = {}
    
    def register_metadata(self, service_type: Type, metadata: Dict[str, Any]) -> None:
        """Register metadata for a service type"""
        self._service_metadata[service_type] = metadata
    
    def get_metadata(self, service_type: Type) -> Optional[Dict[str, Any]]:
        """Get metadata for a service type"""
        return self._service_metadata.get(service_type)
    
    def list_services(self) -> List[Dict[str, Any]]:
        """List all registered services with their metadata"""
        return [
            {
                "service_type": service_type.__name__,
                "metadata": metadata
            }
            for service_type, metadata in self._service_metadata.items()
        ]


# Global registry instance
_registry = ServiceRegistry()

def get_service_registry() -> ServiceRegistry:
    """Get the global service registry instance"""
    return _registry
