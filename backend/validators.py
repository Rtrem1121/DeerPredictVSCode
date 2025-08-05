from typing import Union, Tuple
import numpy as np
from pydantic import BaseModel, validator
from datetime import datetime

class LocationValidator(BaseModel):
    """Validates geographic coordinates"""
    lat: float
    lon: float

    @validator('lat')
    def validate_latitude(cls, v):
        if not -90 <= v <= 90:
            raise ValueError('Latitude must be between -90 and 90 degrees')
        return v

    @validator('lon')
    def validate_longitude(cls, v):
        if not -180 <= v <= 180:
            raise ValueError('Longitude must be between -180 and 180 degrees')
        return v

class PredictionInputValidator(LocationValidator):
    """Validates prediction input parameters"""
    date_time: str
    season: str

    @validator('date_time')
    def validate_datetime(cls, v):
        try:
            datetime.fromisoformat(v)
        except ValueError:
            raise ValueError('date_time must be in ISO format (YYYY-MM-DDTHH:MM:SS)')
        return v

    @validator('season')
    def validate_season(cls, v):
        valid_seasons = ['early_season', 'rut', 'late_season']
        if v.lower() not in valid_seasons:
            raise ValueError(f'season must be one of: {", ".join(valid_seasons)}')
        return v.lower()

def validate_grid_data(grid: np.ndarray, name: str) -> np.ndarray:
    """Validates grid data for analysis"""
    if not isinstance(grid, np.ndarray):
        raise ValueError(f"{name} must be a numpy array")
    
    if grid.ndim != 2:
        raise ValueError(f"{name} must be a 2D array")
    
    if grid.size == 0:
        raise ValueError(f"{name} cannot be empty")
    
    if np.any(np.isnan(grid)):
        raise ValueError(f"{name} contains NaN values")
    
    return grid

def validate_api_response(response_data: dict, api_name: str) -> dict:
    """Validates external API responses"""
    if not isinstance(response_data, dict):
        raise ValueError(f"{api_name} API response must be a dictionary")
    
    if not response_data:
        raise ValueError(f"{api_name} API returned empty response")
    
    return response_data

def safe_percentile(data: np.ndarray, percentile: float, default: float = 0.0) -> float:
    """Safely calculate percentile with fallback"""
    try:
        if data.size == 0:
            return default
        return float(np.percentile(data, percentile))
    except (ValueError, TypeError):
        return default

def clamp_value(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between min and max bounds"""
    return max(min_val, min(value, max_val))
