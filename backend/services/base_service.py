#!/usr/bin/env python3
"""
Base Service Module

Provides base classes and standardized error handling for all services
in the deer prediction application.

Author: System Refactoring
Version: 2.0.0
"""

import logging
from abc import ABC
from enum import Enum
from dataclasses import dataclass
from typing import Optional, TypeVar, Generic, Dict, Any

logger = logging.getLogger(__name__)


class ErrorCode(Enum):
    """Standardized error codes for the application"""
    # Validation errors
    INVALID_COORDINATES = "VALIDATION_001"
    INVALID_DATE_TIME = "VALIDATION_002"
    INVALID_SEASON = "VALIDATION_003"
    MISSING_REQUIRED_FIELD = "VALIDATION_004"
    
    # Terrain analysis errors
    TERRAIN_ANALYSIS_FAILED = "TERRAIN_001"
    ELEVATION_DATA_UNAVAILABLE = "TERRAIN_002"
    ELEVATION_FETCH_FAILED = "TERRAIN_003"
    VEGETATION_DATA_FAILED = "TERRAIN_004"
    TERRAIN_FEATURE_ANALYSIS_FAILED = "TERRAIN_005"
    
    # Weather service errors
    WEATHER_API_UNAVAILABLE = "WEATHER_001"
    WEATHER_DATA_INVALID = "WEATHER_002"
    WEATHER_FORECAST_FAILED = "WEATHER_003"
    
    # Scouting service errors
    SCOUTING_DATA_INVALID = "SCOUTING_001"
    SCOUTING_STORAGE_FAILED = "SCOUTING_002"
    SCOUTING_RETRIEVAL_FAILED = "SCOUTING_003"
    
    # Prediction errors
    PREDICTION_GENERATION_FAILED = "PREDICTION_001"
    MATURE_BUCK_ANALYSIS_FAILED = "PREDICTION_002"
    OPTIMIZED_POINTS_FAILED = "PREDICTION_003"
    
    # External service errors
    EXTERNAL_SERVICE_TIMEOUT = "NETWORK_001"
    EXTERNAL_SERVICE_UNAVAILABLE = "NETWORK_002"
    API_RATE_LIMIT_EXCEEDED = "NETWORK_003"
    
    # Database errors
    DATABASE_CONNECTION_FAILED = "DATABASE_001"
    DATABASE_QUERY_FAILED = "DATABASE_002"
    DATABASE_TRANSACTION_FAILED = "DATABASE_003"
    
    # Cache errors
    CACHE_CONNECTION_FAILED = "CACHE_001"
    CACHE_OPERATION_FAILED = "CACHE_002"
    
    # Configuration errors
    CONFIGURATION_INVALID = "CONFIG_001"
    CONFIGURATION_MISSING = "CONFIG_002"
    
    # Authentication/Authorization errors
    AUTHENTICATION_FAILED = "AUTH_001"
    AUTHORIZATION_FAILED = "AUTH_002"
    INVALID_TOKEN = "AUTH_003"
    
    # General system errors
    UNEXPECTED_ERROR = "SYSTEM_001"
    SERVICE_UNAVAILABLE = "SYSTEM_002"
    RESOURCE_NOT_FOUND = "SYSTEM_003"


@dataclass
class AppError:
    """Standardized error representation"""
    code: ErrorCode
    message: str
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for API responses"""
        return {
            "error_code": self.code.value,
            "message": self.message,
            "details": self.details or {}
        }
    
    def __str__(self) -> str:
        return f"{self.code.value}: {self.message}"


T = TypeVar('T')


class Result(Generic[T]):
    """
    Result type for handling success/failure cases without exceptions
    
    Usage:
        result = some_operation()
        if result.is_success:
            data = result.value
        else:
            error = result.error
    """
    
    def __init__(self, value: Optional[T] = None, error: Optional[AppError] = None):
        if value is not None and error is not None:
            raise ValueError("Result cannot have both value and error")
        if value is None and error is None:
            raise ValueError("Result must have either value or error")
            
        self._value = value
        self._error = error
    
    @property
    def value(self) -> T:
        """Get the success value (raises if called on failure)"""
        if self._error is not None:
            raise ValueError(f"Cannot access value of failed result: {self._error}")
        return self._value
    
    @property
    def error(self) -> AppError:
        """Get the error (raises if called on success)"""
        if self._value is not None:
            raise ValueError("Cannot access error of successful result")
        return self._error
    
    @property
    def is_success(self) -> bool:
        """Check if result represents success"""
        return self._error is None
    
    @property
    def is_failure(self) -> bool:
        """Check if result represents failure"""
        return self._error is not None
    
    def map(self, func):
        """Apply function to value if success, otherwise return error"""
        if self.is_success:
            try:
                return Result(value=func(self.value))
            except Exception as e:
                return Result(error=AppError(
                    ErrorCode.UNEXPECTED_ERROR,
                    f"Error in map operation: {str(e)}"
                ))
        return Result(error=self.error)
    
    def flat_map(self, func):
        """Apply function that returns Result to value if success"""
        if self.is_success:
            return func(self.value)
        return Result(error=self.error)
    
    @classmethod
    def success(cls, value: T) -> 'Result[T]':
        """Create a successful result"""
        return cls(value=value)
    
    @classmethod
    def failure(cls, error: AppError) -> 'Result[T]':
        """Create a failed result"""
        return cls(error=error)


class BaseService(ABC):
    """
    Base class for all services providing common functionality
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def log_operation_start(self, operation: str, **kwargs):
        """Log the start of an operation with context"""
        self.logger.info(f"Starting {operation}", extra={"operation": operation, **kwargs})
    
    def log_operation_success(self, operation: str, **kwargs):
        """Log successful completion of an operation"""
        self.logger.info(f"Completed {operation}", extra={"operation": operation, "status": "success", **kwargs})
    
    def log_operation_failure(self, operation: str, error: AppError, **kwargs):
        """Log failed operation with error details"""
        self.logger.error(
            f"Failed {operation}: {error.message}",
            extra={
                "operation": operation,
                "status": "failure",
                "error_code": error.code.value,
                "error_details": error.details,
                **kwargs
            }
        )
    
    def handle_unexpected_error(self, operation: str, exception: Exception, **context) -> AppError:
        """Handle unexpected exceptions consistently"""
        self.logger.exception(f"Unexpected error in {operation}")
        return AppError(
            ErrorCode.UNEXPECTED_ERROR,
            f"Unexpected error in {operation}: {str(exception)}",
            {
                "operation": operation,
                "exception_type": type(exception).__name__,
                **context
            }
        )


class ServiceHealthCheck:
    """Health check utility for services"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = logging.getLogger(f"{service_name}.health")
    
    async def check_health(self) -> Result[Dict[str, Any]]:
        """Perform health check for the service"""
        try:
            # Override in specific services for custom health checks
            return Result.success({
                "service": self.service_name,
                "status": "healthy",
                "timestamp": logging.time.time()
            })
        except Exception as e:
            return Result.failure(AppError(
                ErrorCode.SERVICE_UNAVAILABLE,
                f"Health check failed for {self.service_name}",
                {"exception": str(e)}
            ))


def create_validation_error(field: str, value: Any, expected: str) -> AppError:
    """Helper function to create validation errors"""
    return AppError(
        ErrorCode.MISSING_REQUIRED_FIELD if value is None else ErrorCode.INVALID_COORDINATES,
        f"Invalid {field}: expected {expected}, got {value}",
        {"field": field, "value": value, "expected": expected}
    )
