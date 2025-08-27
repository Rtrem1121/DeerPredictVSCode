#!/usr/bin/env python3
"""
Scouting Data Models

Pydantic models and data structures for scouting observation system.
Provides type safety and validation for real-world deer sign data.

Author: Vermont Deer Prediction System
Version: 1.0.0
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ObservationType(str, Enum):
    """Enumeration of scouting observation types"""
    FRESH_SCRAPE = "Fresh Scrape"
    RUB_LINE = "Rub Line"
    BEDDING_AREA = "Bedding Area"
    TRAIL_CAMERA = "Trail Camera Setup"
    DEER_TRACKS = "Deer Tracks/Trail"
    FEEDING_SIGN = "Feeding Sign"
    SCAT_DROPPINGS = "Scat/Droppings"
    DEER_SIGHTING = "Deer Sighting"
    OTHER_SIGN = "Other Sign"


class ConfidenceLevel(int, Enum):
    """Confidence levels for observations"""
    UNCERTAIN = 3
    LOW = 4
    MODERATE = 6
    HIGH = 8
    VERY_HIGH = 9
    ABSOLUTE = 10


class ScrapeDetails(BaseModel):
    """Details specific to scrape observations"""
    size: str = Field(..., description="Scrape size: Small, Medium, Large, Huge")
    freshness: str = Field(..., description="How fresh: Old, Recent, Fresh, Very Fresh")
    licking_branch: bool = Field(default=False, description="Active licking branch present")
    multiple_scrapes: bool = Field(default=False, description="Multiple scrapes in area")
    
    @validator('size')
    def validate_size(cls, v):
        valid_sizes = ["Small", "Medium", "Large", "Huge"]
        if v not in valid_sizes:
            raise ValueError(f"Size must be one of: {valid_sizes}")
        return v
    
    @validator('freshness')
    def validate_freshness(cls, v):
        valid_freshness = ["Old", "Recent", "Fresh", "Very Fresh"]
        if v not in valid_freshness:
            raise ValueError(f"Freshness must be one of: {valid_freshness}")
        return v


class RubDetails(BaseModel):
    """Details specific to rub observations"""
    tree_diameter_inches: int = Field(..., ge=1, le=36, description="Tree diameter in inches")
    rub_height_inches: int = Field(..., ge=12, le=72, description="Rub height in inches")
    direction: str = Field(..., description="Primary rub direction")
    tree_species: Optional[str] = Field(None, description="Type of tree if known")
    multiple_rubs: bool = Field(default=False, description="Multiple rubs in line")
    
    @validator('direction')
    def validate_direction(cls, v):
        valid_directions = ["North", "South", "East", "West", "Northeast", "Northwest", 
                           "Southeast", "Southwest", "Multiple"]
        if v not in valid_directions:
            raise ValueError(f"Direction must be one of: {valid_directions}")
        return v


class BeddingDetails(BaseModel):
    """Details specific to bedding area observations"""
    number_of_beds: int = Field(..., ge=1, le=20, description="Number of beds found")
    bed_size: str = Field(..., description="Bed size category")
    cover_type: str = Field(..., description="Type of cover")
    visibility: str = Field(..., description="Visibility from bed")
    escape_routes: int = Field(..., ge=1, le=8, description="Number of escape routes")
    
    @validator('bed_size')
    def validate_bed_size(cls, v):
        valid_sizes = ["Small (doe/fawn)", "Medium (young buck)", "Large (mature buck)", "Mixed sizes"]
        if v not in valid_sizes:
            raise ValueError(f"Bed size must be one of: {valid_sizes}")
        return v


class TrailCameraDetails(BaseModel):
    """Details specific to trail camera observations"""
    camera_brand: Optional[str] = Field(None, description="Camera brand/model")
    setup_date: datetime = Field(..., description="When camera was set up")
    total_photos: int = Field(default=0, ge=0, description="Total photos captured")
    deer_photos: int = Field(default=0, ge=0, description="Photos with deer")
    mature_buck_photos: int = Field(default=0, ge=0, description="Photos with mature bucks")
    peak_activity_time: Optional[str] = Field(None, description="Peak activity time if known")
    battery_level: Optional[int] = Field(None, ge=0, le=100, description="Battery percentage")
    
    @validator('deer_photos')
    def validate_deer_photos(cls, v, values):
        if 'total_photos' in values and v > values['total_photos']:
            raise ValueError("Deer photos cannot exceed total photos")
        return v


class TracksDetails(BaseModel):
    """Details specific to deer tracks observations"""
    track_size_inches: float = Field(..., ge=1.0, le=6.0, description="Track length in inches")
    track_depth: str = Field(..., description="Track depth category")
    number_of_tracks: int = Field(..., ge=1, le=100, description="Number of tracks visible")
    direction_of_travel: str = Field(..., description="Direction deer were traveling")
    gait_pattern: str = Field(..., description="Walking, trotting, or running")
    
    @validator('track_depth')
    def validate_track_depth(cls, v):
        valid_depths = ["Shallow", "Medium", "Deep", "Very Deep"]
        if v not in valid_depths:
            raise ValueError(f"Track depth must be one of: {valid_depths}")
        return v


class ScoutingObservation(BaseModel):
    """Main scouting observation model"""
    id: Optional[str] = Field(None, description="Unique observation ID")
    lat: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    lon: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    observation_type: ObservationType = Field(..., description="Type of observation")
    
    # Type-specific details (only one should be populated)
    scrape_details: Optional[ScrapeDetails] = None
    rub_details: Optional[RubDetails] = None
    bedding_details: Optional[BeddingDetails] = None
    camera_details: Optional[TrailCameraDetails] = None
    tracks_details: Optional[TracksDetails] = None
    
    # Common fields
    notes: str = Field(default="", description="Additional notes")
    confidence: int = Field(..., ge=1, le=10, description="Confidence level 1-10")
    timestamp: datetime = Field(default_factory=datetime.now, description="When observed")
    photo_urls: List[str] = Field(default_factory=list, description="URLs to photos")
    weather_conditions: Optional[str] = Field(None, description="Weather when observed")
    
    # Validation
    @validator('confidence')
    def validate_confidence(cls, v):
        if not 1 <= v <= 10:
            raise ValueError("Confidence must be between 1 and 10")
        return v
    
    @validator('photo_urls')
    def validate_photo_urls(cls, v):
        if len(v) > 10:
            raise ValueError("Maximum 10 photos per observation")
        return v
    
    def get_details(self) -> Optional[BaseModel]:
        """Get the type-specific details for this observation"""
        detail_map = {
            ObservationType.FRESH_SCRAPE: self.scrape_details,
            ObservationType.RUB_LINE: self.rub_details,
            ObservationType.BEDDING_AREA: self.bedding_details,
            ObservationType.TRAIL_CAMERA: self.camera_details,
            ObservationType.DEER_TRACKS: self.tracks_details,
        }
        return detail_map.get(self.observation_type)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = self.dict()
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScoutingObservation':
        """Create from dictionary"""
        if isinstance(data.get('timestamp'), str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class ScoutingObservationResponse(BaseModel):
    """Response model for scouting observation operations"""
    status: str = Field(..., description="Operation status")
    observation_id: Optional[str] = Field(None, description="ID of created/updated observation")
    message: str = Field(..., description="Status message")
    confidence_boost: Optional[float] = Field(None, description="Confidence boost applied")


class ScoutingQuery(BaseModel):
    """Query parameters for retrieving scouting observations"""
    lat: float = Field(..., ge=-90, le=90, description="Center latitude")
    lon: float = Field(..., ge=-180, le=180, description="Center longitude")
    radius_miles: float = Field(default=2.0, ge=0.1, le=50.0, description="Search radius in miles")
    observation_types: Optional[List[ObservationType]] = Field(None, description="Filter by types")
    min_confidence: Optional[int] = Field(None, ge=1, le=10, description="Minimum confidence")
    days_back: Optional[int] = Field(None, ge=1, le=365, description="Only include last N days")


class ScoutingAnalytics(BaseModel):
    """Analytics data for scouting observations"""
    total_observations: int = Field(..., description="Total number of observations")
    observations_by_type: Dict[str, int] = Field(..., description="Count by observation type")
    average_confidence: float = Field(..., description="Average confidence score")
    most_recent_observation: Optional[datetime] = Field(None, description="Most recent observation date")
    prediction_accuracy: Optional[float] = Field(None, description="How often predictions matched reality")
    hottest_areas: List[Dict[str, Any]] = Field(default_factory=list, description="Areas with most sign")
