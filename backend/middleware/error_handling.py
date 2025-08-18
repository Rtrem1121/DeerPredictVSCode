#!/usr/bin/env python3
"""
Error Handling Middleware

Comprehensive error handling middleware for the deer prediction application.
Provides structured error responses, logging, and monitoring integration.

Key Features:
- Structured error responses
- Detailed logging with context
- Performance monitoring
- Security considerations
- User-friendly error messages

Author: GitHub Copilot
Version: 1.0.0
Date: August 14, 2025
"""

import logging
import traceback
import time
from typing import Any, Callable, Dict, Optional
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class ErrorType(str, Enum):
    """Enumeration of error types for classification"""
    VALIDATION_ERROR = "validation_error"
    BUSINESS_LOGIC_ERROR = "business_logic_error"
    EXTERNAL_SERVICE_ERROR = "external_service_error"
    SYSTEM_ERROR = "system_error"
    AUTHENTICATION_ERROR = "authentication_error"
    AUTHORIZATION_ERROR = "authorization_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    NOT_FOUND_ERROR = "not_found_error"


class ErrorSeverity(str, Enum):
    """Error severity levels for monitoring and alerting"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorResponse(BaseModel):
    """Structured error response model"""
    error_id: str = Field(..., description="Unique error identifier for tracking")
    error_type: ErrorType = Field(..., description="Classification of the error")
    severity: ErrorSeverity = Field(..., description="Error severity level")
    message: str = Field(..., description="User-friendly error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: str = Field(..., description="ISO timestamp when error occurred")
    path: str = Field(..., description="API endpoint where error occurred")
    request_id: Optional[str] = Field(None, description="Request correlation ID")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "error_id": "550e8400-e29b-41d4-a716-446655440000",
                "error_type": "business_logic_error",
                "severity": "medium",
                "message": "Unable to generate prediction for the specified location",
                "details": {
                    "reason": "Insufficient terrain data available",
                    "suggested_action": "Try a different location or contact support"
                },
                "timestamp": "2025-08-14T22:30:00.000Z",
                "path": "/predict",
                "request_id": "req_123456"
            }
        }
    }


class AppException(Exception):
    """Base application exception with error classification"""
    
    def __init__(
        self,
        message: str,
        error_type: ErrorType = ErrorType.SYSTEM_ERROR,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        self.message = message
        self.error_type = error_type
        self.severity = severity
        self.details = details or {}
        self.cause = cause
        super().__init__(message)


class ValidationError(AppException):
    """Validation related errors"""
    
    def __init__(self, message: str, field: str = None, value: Any = None):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["invalid_value"] = str(value)
            
        super().__init__(
            message=message,
            error_type=ErrorType.VALIDATION_ERROR,
            severity=ErrorSeverity.LOW,
            details=details
        )


class BusinessLogicError(AppException):
    """Business logic related errors"""
    
    def __init__(self, message: str, operation: str = None, details: Dict[str, Any] = None):
        error_details = details or {}
        if operation:
            error_details["operation"] = operation
            
        super().__init__(
            message=message,
            error_type=ErrorType.BUSINESS_LOGIC_ERROR,
            severity=ErrorSeverity.MEDIUM,
            details=error_details
        )


class ExternalServiceError(AppException):
    """External service integration errors"""
    
    def __init__(self, message: str, service: str, status_code: int = None, details: Dict[str, Any] = None):
        error_details = details or {}
        error_details["service"] = service
        if status_code:
            error_details["status_code"] = status_code
            
        # Determine severity based on service criticality
        severity = ErrorSeverity.HIGH if service in ["weather_api", "terrain_api"] else ErrorSeverity.MEDIUM
        
        super().__init__(
            message=message,
            error_type=ErrorType.EXTERNAL_SERVICE_ERROR,
            severity=severity,
            details=error_details
        )


class SystemError(AppException):
    """System-level errors"""
    
    def __init__(self, message: str, component: str = None, details: Dict[str, Any] = None):
        error_details = details or {}
        if component:
            error_details["component"] = component
            
        super().__init__(
            message=message,
            error_type=ErrorType.SYSTEM_ERROR,
            severity=ErrorSeverity.HIGH,
            details=error_details
        )


class ErrorHandlingMiddleware:
    """
    Comprehensive error handling middleware for FastAPI applications.
    
    Features:
    - Structured error responses
    - Detailed logging with context
    - Performance metrics
    - Security considerations
    - User-friendly error messages
    """
    
    def __init__(self, app):
        self.app = app
        self.error_counts = {}
        self.performance_metrics = {}
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Process request with comprehensive error handling"""
        
        # Generate request correlation ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Start timing
        start_time = time.time()
        
        try:
            # Add request context to logs
            logger.info(
                f"Request started",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "query_params": str(request.query_params),
                    "client_ip": request.client.host if request.client else "unknown"
                }
            )
            
            # Process request
            response = await call_next(request)
            
            # Log successful completion
            duration = time.time() - start_time
            logger.info(
                f"Request completed successfully",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "duration_ms": round(duration * 1000, 2)
                }
            )
            
            # Update performance metrics
            self._update_performance_metrics(request.url.path, duration, True)
            
            return response
            
        except AppException as e:
            # Handle custom application exceptions
            return await self._handle_app_exception(request, e, start_time)
            
        except HTTPException as e:
            # Handle FastAPI HTTP exceptions
            return await self._handle_http_exception(request, e, start_time)
            
        except Exception as e:
            # Handle unexpected system errors
            return await self._handle_system_exception(request, e, start_time)
    
    async def _handle_app_exception(self, request: Request, error: AppException, start_time: float) -> JSONResponse:
        """Handle custom application exceptions"""
        
        error_id = str(uuid.uuid4())
        duration = time.time() - start_time
        
        # Log error with context
        log_extra = {
            "error_id": error_id,
            "request_id": getattr(request.state, 'request_id', 'unknown'),
            "error_type": error.error_type.value,
            "severity": error.severity.value,
            "path": request.url.path,
            "duration_ms": round(duration * 1000, 2)
        }
        
        if error.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            logger.error(f"Application error: {error.message}", extra=log_extra, exc_info=error.cause)
        else:
            logger.warning(f"Application error: {error.message}", extra=log_extra)
        
        # Update error metrics
        self._update_error_metrics(error.error_type, error.severity)
        self._update_performance_metrics(request.url.path, duration, False)
        
        # Build error response
        error_response = ErrorResponse(
            error_id=error_id,
            error_type=error.error_type,
            severity=error.severity,
            message=self._get_user_friendly_message(error),
            details=self._sanitize_error_details(error.details),
            timestamp=time.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            path=request.url.path,
            request_id=getattr(request.state, 'request_id', None)
        )
        
        # Map severity to HTTP status codes
        status_code = self._get_status_code_for_error_type(error.error_type)
        
        return JSONResponse(
            status_code=status_code,
            content=error_response.dict()
        )
    
    async def _handle_http_exception(self, request: Request, error: HTTPException, start_time: float) -> JSONResponse:
        """Handle FastAPI HTTP exceptions"""
        
        error_id = str(uuid.uuid4())
        duration = time.time() - start_time
        
        # Map HTTP status to error type
        error_type = self._map_http_status_to_error_type(error.status_code)
        severity = ErrorSeverity.LOW if error.status_code < 500 else ErrorSeverity.HIGH
        
        # Log error
        log_extra = {
            "error_id": error_id,
            "request_id": getattr(request.state, 'request_id', 'unknown'),
            "status_code": error.status_code,
            "path": request.url.path,
            "duration_ms": round(duration * 1000, 2)
        }
        
        logger.warning(f"HTTP error {error.status_code}: {error.detail}", extra=log_extra)
        
        # Update metrics
        self._update_error_metrics(error_type, severity)
        self._update_performance_metrics(request.url.path, duration, False)
        
        # Build error response
        error_response = ErrorResponse(
            error_id=error_id,
            error_type=error_type,
            severity=severity,
            message=str(error.detail),
            details={"status_code": error.status_code},
            timestamp=time.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            path=request.url.path,
            request_id=getattr(request.state, 'request_id', None)
        )
        
        return JSONResponse(
            status_code=error.status_code,
            content=error_response.dict()
        )
    
    async def _handle_system_exception(self, request: Request, error: Exception, start_time: float) -> JSONResponse:
        """Handle unexpected system exceptions"""
        
        error_id = str(uuid.uuid4())
        duration = time.time() - start_time
        
        # Log system error with full traceback
        log_extra = {
            "error_id": error_id,
            "request_id": getattr(request.state, 'request_id', 'unknown'),
            "error_type": type(error).__name__,
            "path": request.url.path,
            "duration_ms": round(duration * 1000, 2)
        }
        
        logger.error(
            f"Unexpected system error: {str(error)}", 
            extra=log_extra, 
            exc_info=True
        )
        
        # Update metrics
        self._update_error_metrics(ErrorType.SYSTEM_ERROR, ErrorSeverity.CRITICAL)
        self._update_performance_metrics(request.url.path, duration, False)
        
        # Build generic error response (don't expose internal details)
        error_response = ErrorResponse(
            error_id=error_id,
            error_type=ErrorType.SYSTEM_ERROR,
            severity=ErrorSeverity.CRITICAL,
            message="An unexpected error occurred. Please try again later.",
            details={
                "support_reference": error_id,
                "suggested_action": "If the problem persists, please contact support with the error ID"
            },
            timestamp=time.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            path=request.url.path,
            request_id=getattr(request.state, 'request_id', None)
        )
        
        return JSONResponse(
            status_code=500,
            content=error_response.dict()
        )
    
    def _get_user_friendly_message(self, error: AppException) -> str:
        """Convert technical error messages to user-friendly ones"""
        
        user_friendly_messages = {
            "terrain analysis failed": "Unable to analyze terrain data for this location",
            "weather data unavailable": "Weather information is temporarily unavailable",
            "invalid coordinates": "The specified location coordinates are invalid",
            "prediction timeout": "The prediction is taking longer than expected, please try again",
            "insufficient data": "Not enough data available to generate a reliable prediction"
        }
        
        # Look for patterns in error message
        message_lower = error.message.lower()
        for pattern, friendly_message in user_friendly_messages.items():
            if pattern in message_lower:
                return friendly_message
        
        # Return original message if no mapping found
        return error.message
    
    def _sanitize_error_details(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive information from error details"""
        if not details:
            return {}
        
        # Remove sensitive keys
        sensitive_keys = ['password', 'token', 'key', 'secret', 'credential']
        sanitized = {}
        
        for key, value in details.items():
            if any(sensitive_key in key.lower() for sensitive_key in sensitive_keys):
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _get_status_code_for_error_type(self, error_type: ErrorType) -> int:
        """Map error types to appropriate HTTP status codes"""
        
        status_mapping = {
            ErrorType.VALIDATION_ERROR: 400,
            ErrorType.AUTHENTICATION_ERROR: 401,
            ErrorType.AUTHORIZATION_ERROR: 403,
            ErrorType.NOT_FOUND_ERROR: 404,
            ErrorType.BUSINESS_LOGIC_ERROR: 422,
            ErrorType.RATE_LIMIT_ERROR: 429,
            ErrorType.EXTERNAL_SERVICE_ERROR: 502,
            ErrorType.SYSTEM_ERROR: 500
        }
        
        return status_mapping.get(error_type, 500)
    
    def _map_http_status_to_error_type(self, status_code: int) -> ErrorType:
        """Map HTTP status codes to error types"""
        
        status_mapping = {
            400: ErrorType.VALIDATION_ERROR,
            401: ErrorType.AUTHENTICATION_ERROR,
            403: ErrorType.AUTHORIZATION_ERROR,
            404: ErrorType.NOT_FOUND_ERROR,
            422: ErrorType.VALIDATION_ERROR,
            429: ErrorType.RATE_LIMIT_ERROR,
            500: ErrorType.SYSTEM_ERROR,
            502: ErrorType.EXTERNAL_SERVICE_ERROR,
            503: ErrorType.EXTERNAL_SERVICE_ERROR
        }
        
        return status_mapping.get(status_code, ErrorType.SYSTEM_ERROR)
    
    def _update_error_metrics(self, error_type: ErrorType, severity: ErrorSeverity):
        """Update error tracking metrics"""
        
        key = f"{error_type.value}_{severity.value}"
        self.error_counts[key] = self.error_counts.get(key, 0) + 1
        
        # Log metrics for monitoring systems
        logger.info(
            f"Error metrics updated",
            extra={
                "metric_type": "error_count",
                "error_type": error_type.value,
                "severity": severity.value,
                "count": self.error_counts[key]
            }
        )
    
    def _update_performance_metrics(self, path: str, duration: float, success: bool):
        """Update performance tracking metrics"""
        
        if path not in self.performance_metrics:
            self.performance_metrics[path] = {
                "total_requests": 0,
                "successful_requests": 0,
                "total_duration": 0.0,
                "max_duration": 0.0,
                "min_duration": float('inf')
            }
        
        metrics = self.performance_metrics[path]
        metrics["total_requests"] += 1
        
        if success:
            metrics["successful_requests"] += 1
        
        metrics["total_duration"] += duration
        metrics["max_duration"] = max(metrics["max_duration"], duration)
        metrics["min_duration"] = min(metrics["min_duration"], duration)
        
        # Log performance metrics periodically
        if metrics["total_requests"] % 100 == 0:  # Every 100 requests
            avg_duration = metrics["total_duration"] / metrics["total_requests"]
            success_rate = metrics["successful_requests"] / metrics["total_requests"]
            
            logger.info(
                f"Performance metrics",
                extra={
                    "metric_type": "performance",
                    "path": path,
                    "avg_duration_ms": round(avg_duration * 1000, 2),
                    "success_rate": round(success_rate * 100, 2),
                    "total_requests": metrics["total_requests"]
                }
            )
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get current error metrics summary"""
        return {
            "error_counts": self.error_counts.copy(),
            "performance_metrics": self.performance_metrics.copy(),
            "timestamp": time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        }


# Factory function
def create_error_handling_middleware():
    """Create and configure error handling middleware"""
    return ErrorHandlingMiddleware
