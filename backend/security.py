"""
Input validation and security utilities.
Provides secure input validation, sanitization, and security helpers.
"""
import re
import logging
from typing import Union, Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, validator, Field
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

# Vermont's approximate bounding box for coordinate validation
VERMONT_BOUNDS = {
    'min_lat': 42.730,   # Southern border
    'max_lat': 45.017,   # Northern border  
    'min_lon': -73.438,  # Eastern border
    'max_lon': -71.465   # Western border
}

# Allowed seasons for deer hunting
VALID_SEASONS = ["early_season", "rut", "late_season"]

# Input sanitization patterns
SAFE_STRING_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-_.,:()]+$')
COORDINATE_PATTERN = re.compile(r'^-?\d+\.?\d*$')


class ValidationError(Exception):
    """Custom validation error"""
    pass


class SecurityError(Exception):
    """Custom security error"""
    pass


class CoordinateValidator:
    """Validates geographic coordinates"""
    
    @staticmethod
    def validate_latitude(lat: float) -> float:
        """
        Validate latitude coordinate.
        
        Args:
            lat: Latitude value
            
        Returns:
            float: Validated latitude
            
        Raises:
            ValidationError: If latitude is invalid
        """
        if not isinstance(lat, (int, float)):
            raise ValidationError("Latitude must be a number")
            
        if not -90 <= lat <= 90:
            raise ValidationError("Latitude must be between -90 and 90 degrees")
            
        return float(lat)
    
    @staticmethod
    def validate_longitude(lon: float) -> float:
        """
        Validate longitude coordinate.
        
        Args:
            lon: Longitude value
            
        Returns:
            float: Validated longitude
            
        Raises:
            ValidationError: If longitude is invalid
        """
        if not isinstance(lon, (int, float)):
            raise ValidationError("Longitude must be a number")
            
        if not -180 <= lon <= 180:
            raise ValidationError("Longitude must be between -180 and 180 degrees")
            
        return float(lon)
    
    @staticmethod
    def validate_vermont_coordinates(lat: float, lon: float) -> tuple[float, float]:
        """
        Validate coordinates are within Vermont boundaries.
        
        Args:
            lat: Latitude value
            lon: Longitude value
            
        Returns:
            tuple[float, float]: Validated coordinates
            
        Raises:
            ValidationError: If coordinates are outside Vermont
        """
        validated_lat = CoordinateValidator.validate_latitude(lat)
        validated_lon = CoordinateValidator.validate_longitude(lon)
        
        if not (VERMONT_BOUNDS['min_lat'] <= validated_lat <= VERMONT_BOUNDS['max_lat']):
            raise ValidationError(
                f"Latitude {validated_lat} is outside Vermont boundaries "
                f"({VERMONT_BOUNDS['min_lat']} to {VERMONT_BOUNDS['max_lat']})"
            )
            
        if not (VERMONT_BOUNDS['min_lon'] <= validated_lon <= VERMONT_BOUNDS['max_lon']):
            raise ValidationError(
                f"Longitude {validated_lon} is outside Vermont boundaries "
                f"({VERMONT_BOUNDS['min_lon']} to {VERMONT_BOUNDS['max_lon']})"
            )
            
        return validated_lat, validated_lon


class DateTimeValidator:
    """Validates date and time inputs"""
    
    @staticmethod
    def validate_datetime_string(datetime_str: str) -> datetime:
        """
        Validate and parse datetime string.
        
        Args:
            datetime_str: Datetime string in ISO format
            
        Returns:
            datetime: Parsed datetime object
            
        Raises:
            ValidationError: If datetime string is invalid
        """
        if not isinstance(datetime_str, str):
            raise ValidationError("Datetime must be a string")
            
        try:
            # Try parsing ISO format first
            return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        except ValueError:
            # Try common formats
            formats = [
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d",
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(datetime_str, fmt)
                except ValueError:
                    continue
                    
            raise ValidationError(f"Invalid datetime format: {datetime_str}")


class SeasonValidator:
    """Validates hunting season inputs"""
    
    @staticmethod
    def validate_season(season: str) -> str:
        """
        Validate hunting season.
        
        Args:
            season: Season string
            
        Returns:
            str: Validated season
            
        Raises:
            ValidationError: If season is invalid
        """
        if not isinstance(season, str):
            raise ValidationError("Season must be a string")
            
        season = season.lower().strip()
        
        if season not in VALID_SEASONS:
            raise ValidationError(
                f"Invalid season '{season}'. Valid seasons: {', '.join(VALID_SEASONS)}"
            )
            
        return season


class InputSanitizer:
    """Sanitizes user inputs for security"""
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 255) -> str:
        """
        Sanitize string input to prevent injection attacks.
        
        Args:
            value: String to sanitize
            max_length: Maximum allowed length
            
        Returns:
            str: Sanitized string
            
        Raises:
            SecurityError: If string contains unsafe characters
        """
        if not isinstance(value, str):
            raise SecurityError("Value must be a string")
            
        if len(value) > max_length:
            raise SecurityError(f"String too long (max {max_length} characters)")
            
        # Remove potentially dangerous characters
        sanitized = value.strip()
        
        # Check for unsafe patterns
        if not SAFE_STRING_PATTERN.match(sanitized):
            raise SecurityError("String contains unsafe characters")
            
        return sanitized
    
    @staticmethod
    def sanitize_numeric_string(value: str) -> str:
        """
        Sanitize numeric string input.
        
        Args:
            value: Numeric string to sanitize
            
        Returns:
            str: Sanitized numeric string
            
        Raises:
            SecurityError: If string is not a valid number
        """
        if not isinstance(value, str):
            raise SecurityError("Value must be a string")
            
        sanitized = value.strip()
        
        if not COORDINATE_PATTERN.match(sanitized):
            raise SecurityError("Invalid numeric format")
            
        return sanitized


# Pydantic models with built-in validation
class PredictionRequest(BaseModel):
    """Validated prediction request model"""
    lat: float = Field(..., description="Latitude coordinate")
    lon: float = Field(..., description="Longitude coordinate") 
    date_time: str = Field(..., description="Date and time in ISO format")
    season: str = Field(..., description="Hunting season")
    suggestion_threshold: float = Field(default=6.0, description="Threshold for suggesting better spots")
    min_suggestion_rating: float = Field(default=7.0, description="Minimum rating for suggested spots")
    
    @validator('lat')
    def validate_latitude(cls, v):
        return CoordinateValidator.validate_latitude(v)
    
    @validator('lon')
    def validate_longitude(cls, v):
        return CoordinateValidator.validate_longitude(v)
        
    @validator('lat', 'lon', pre=False, always=True)
    def validate_vermont_bounds(cls, v, values):
        if 'lat' in values and 'lon' in values:
            CoordinateValidator.validate_vermont_coordinates(
                values['lat'], values['lon']
            )
        return v
    
    @validator('date_time')
    def validate_datetime(cls, v):
        DateTimeValidator.validate_datetime_string(v)
        return v
    
    @validator('season')
    def validate_season(cls, v):
        return SeasonValidator.validate_season(v)


class SecurityMiddleware:
    """Security middleware for request validation"""
    
    def __init__(self, enable_rate_limiting: bool = True):
        self.enable_rate_limiting = enable_rate_limiting
        self.request_counts: Dict[str, List[datetime]] = {}
    
    def validate_request_rate(self, client_ip: str, max_requests: int = 60) -> None:
        """
        Validate request rate limiting.
        
        Args:
            client_ip: Client IP address
            max_requests: Maximum requests per minute
            
        Raises:
            HTTPException: If rate limit exceeded
        """
        if not self.enable_rate_limiting:
            return
            
        now = datetime.now()
        minute_ago = datetime.now().replace(second=0, microsecond=0)
        
        # Initialize client tracking
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []
        
        # Remove old requests (older than 1 minute)
        self.request_counts[client_ip] = [
            req_time for req_time in self.request_counts[client_ip]
            if req_time >= minute_ago
        ]
        
        # Check rate limit
        if len(self.request_counts[client_ip]) >= max_requests:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later."
            )
        
        # Add current request
        self.request_counts[client_ip].append(now)
    
    def validate_request_headers(self, headers: Dict[str, str]) -> None:
        """
        Validate request headers for security.
        
        Args:
            headers: Request headers
            
        Raises:
            HTTPException: If headers are suspicious
        """
        # Check for common attack patterns in headers
        suspicious_patterns = [
            r'<script',
            r'javascript:',
            r'eval\(',
            r'expression\(',
            r'vbscript:',
            r'onclick',
            r'onerror',
        ]
        
        for header_name, header_value in headers.items():
            header_value_lower = header_value.lower()
            for pattern in suspicious_patterns:
                if re.search(pattern, header_value_lower):
                    logger.warning(f"Suspicious header detected: {header_name}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid request headers"
                    )


def create_security_middleware(settings) -> SecurityMiddleware:
    """
    Create security middleware with settings.
    
    Args:
        settings: Application settings
        
    Returns:
        SecurityMiddleware: Configured security middleware
    """
    return SecurityMiddleware(
        enable_rate_limiting=settings.security.rate_limiting_enabled
    )


def handle_validation_error(error: ValidationError) -> HTTPException:
    """
    Convert validation error to HTTP exception.
    
    Args:
        error: Validation error
        
    Returns:
        HTTPException: HTTP 400 exception
    """
    logger.warning(f"Validation error: {error}")
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(error)
    )


def handle_security_error(error: SecurityError) -> HTTPException:
    """
    Convert security error to HTTP exception.
    
    Args:
        error: Security error
        
    Returns:
        HTTPException: HTTP 400 exception
    """
    logger.warning(f"Security error: {error}")
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid request data"
    )
