from typing import Union, Tuple, List, Any
from dataclasses import dataclass, field
import numpy as np
from pydantic import BaseModel, validator
from datetime import datetime
import math

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


@dataclass
class ValidationIssue:
    category: str
    severity: str
    description: str
    affected_elements: List[str] = field(default_factory=list)


@dataclass
class ValidationReport:
    issues: List[ValidationIssue]
    overall_quality_score: float
    is_valid: bool
    recommendations: List[str]


class PredictionQualityValidator:
    """Validate prediction quality for stand/bedding/wind alignment."""

    WIND_TOLERANCE_DEG = 30.0
    OPTIMAL_STAND_DISTANCE_M = (100, 250)
    ASPECT_TOLERANCE_DEG = 45.0
    MIN_QUALITY_THRESHOLD = 70.0

    @staticmethod
    def _bearing_between(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        lat1_rad, lat2_rad = math.radians(lat1), math.radians(lat2)
        delta_lon = math.radians(lon2 - lon1)
        y_val = math.sin(delta_lon) * math.cos(lat2_rad)
        x_val = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon)
        return (math.degrees(math.atan2(y_val, x_val)) + 360) % 360

    @staticmethod
    def _angular_difference(angle_a: float, angle_b: float) -> float:
        return abs(((angle_a - angle_b + 180) % 360) - 180)

    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        radius_m = 6_371_000
        lat1_rad, lon1_rad = math.radians(lat1), math.radians(lon1)
        lat2_rad, lon2_rad = math.radians(lat2), math.radians(lon2)
        delta_lat = lat2_rad - lat1_rad
        delta_lon = lon2_rad - lon1_rad
        a_val = (
            math.sin(delta_lat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        )
        c_val = 2 * math.atan2(math.sqrt(a_val), math.sqrt(max(1 - a_val, 0)))
        return radius_m * c_val

    @classmethod
    def validate(cls, prediction: dict) -> ValidationReport:
        issues: List[ValidationIssue] = []
        recommendations: List[str] = []
        score = 100.0

        if not isinstance(prediction, dict):
            return ValidationReport(
                issues=[ValidationIssue(
                    category="structure",
                    severity="error",
                    description="Prediction payload must be a dictionary",
                    affected_elements=[]
                )],
                overall_quality_score=0.0,
                is_valid=False,
                recommendations=["Provide a structured prediction response."]
            )

        stands = prediction.get("mature_buck_analysis", {}).get("stand_recommendations", []) or []
        beds = prediction.get("bedding_zones", {}).get("features", []) or []
        wind_direction = prediction.get("weather_data", {}).get("wind_direction")

        try:
            wind_direction = float(wind_direction)
        except (TypeError, ValueError):
            wind_direction = None

        scent_bearing = None
        if wind_direction is not None:
            scent_bearing = (wind_direction + 180) % 360

        # Scent cone validation
        if scent_bearing is not None:
            for stand in stands:
                stand_coords = stand.get("coordinates", {}) or {}
                stand_lat = stand_coords.get("lat")
                stand_lon = stand_coords.get("lon")
                if stand_lat is None or stand_lon is None:
                    continue
                for bed in beds:
                    bed_coords = (bed.get("geometry", {}) or {}).get("coordinates") or []
                    if len(bed_coords) < 2:
                        continue
                    bed_lon, bed_lat = bed_coords[0], bed_coords[1]
                    try:
                        bearing = cls._bearing_between(float(stand_lat), float(stand_lon), float(bed_lat), float(bed_lon))
                    except (TypeError, ValueError):
                        continue
                    angle_diff = cls._angular_difference(bearing, scent_bearing)
                    if angle_diff <= cls.WIND_TOLERANCE_DEG:
                        issues.append(ValidationIssue(
                            category="scent_cone",
                            severity="error",
                            description="Stand scent cone overlaps bedding area",
                            affected_elements=[
                                stand.get("stand_id", "stand"),
                                (bed.get("properties", {}) or {}).get("id", "bedding")
                            ]
                        ))
                        recommendations.append("Reposition stand downwind of bedding zones.")
                        score -= 20
                        break

        # Stand distance validation
        optimal_min, optimal_max = cls.OPTIMAL_STAND_DISTANCE_M
        for stand in stands:
            stand_coords = stand.get("coordinates", {}) or {}
            stand_lat = stand_coords.get("lat")
            stand_lon = stand_coords.get("lon")
            if stand_lat is None or stand_lon is None:
                continue
            for bed in beds:
                bed_coords = (bed.get("geometry", {}) or {}).get("coordinates") or []
                if len(bed_coords) < 2:
                    continue
                bed_lon, bed_lat = bed_coords[0], bed_coords[1]
                try:
                    distance_m = cls._haversine_distance(float(stand_lat), float(stand_lon), float(bed_lat), float(bed_lon))
                except (TypeError, ValueError):
                    continue
                if distance_m < optimal_min or distance_m > optimal_max:
                    issues.append(ValidationIssue(
                        category="stand_distance",
                        severity="warning",
                        description="Stand distance outside optimal range",
                        affected_elements=[stand.get("stand_id", "stand")]
                    ))
                    recommendations.append("Adjust stand distance to 100–250m from bedding zones.")
                    score -= 5
                    break

        score = max(0.0, min(100.0, score))
        is_valid = score >= cls.MIN_QUALITY_THRESHOLD and not any(
            issue.severity == "error" for issue in issues
        )

        return ValidationReport(
            issues=issues,
            overall_quality_score=float(score),
            is_valid=is_valid,
            recommendations=list(dict.fromkeys(recommendations))
        )
