"""
Bedding Site Domain Models

Defines bedding zone structures with Vermont whitetail deer ecology integration.
Supports primary/secondary/escape zone categorization and biological scoring.

References:
- Nelson & Mech (1981): Bedding site selection and thermoregulation
- Marchinton & Hirth (1984): Mature buck bedding patterns
- Hirth (1977): Scent-based predator detection
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from enum import Enum


class BeddingZoneType(Enum):
    """Bedding zone categorization based on distance from core area."""
    PRIMARY = "primary"  # 0-100m: Core bedding, thick cover
    SECONDARY = "secondary"  # 100-250m: Alternate sites, escape routes
    ESCAPE = "escape"  # 250-500m: Transition zones, edge habitat


@dataclass
class BeddingScoreBreakdown:
    """
    Detailed scoring breakdown for biological validation.
    
    Tracks individual components contributing to final bedding score
    to enable troubleshooting and biological interpretation.
    """
    
    # Core terrain scores
    slope_score: float = 0.0  # 10-30° optimal (drainage + visibility)
    aspect_score: float = 0.0  # Wind-integrated or thermal-based
    elevation_score: float = 0.0  # Relative to surrounding terrain
    
    # Habitat quality scores
    canopy_score: float = 0.0  # >60% coverage for security
    food_score: float = 0.0  # Mast crops in fall, browse in winter
    
    # Security factors
    road_distance_score: float = 0.0  # >200m from roads (disturbance proxy)
    escape_routes_score: float = 0.0  # Multiple exits via benches/ridges
    
    # Wind/thermal analysis
    thermal_wind_score: float = 0.0  # Upslope/downslope thermal drafts
    scent_management_score: float = 0.0  # Wind-based predator detection
    
    # Composite scores
    terrain_composite: float = 0.0  # Weighted slope + aspect + elevation
    habitat_composite: float = 0.0  # Weighted canopy + food
    security_composite: float = 0.0  # Weighted road + escape + scent
    
    # Final score
    total_score: float = 0.0  # 0-100 weighted composite
    
    # Biological reasoning
    primary_factors: List[str] = field(default_factory=list)  # Top 3 positive factors
    limiting_factors: List[str] = field(default_factory=list)  # Top 3 negative factors
    
    def get_summary(self) -> str:
        """Generate human-readable scoring summary."""
        summary = f"Total Score: {self.total_score:.1f}/100\n"
        summary += f"  Terrain: {self.terrain_composite:.1f} (slope={self.slope_score:.0f}, aspect={self.aspect_score:.0f})\n"
        summary += f"  Habitat: {self.habitat_composite:.1f} (canopy={self.canopy_score:.0f}, food={self.food_score:.0f})\n"
        summary += f"  Security: {self.security_composite:.1f} (road={self.road_distance_score:.0f}, scent={self.scent_management_score:.0f})\n"
        
        if self.primary_factors:
            summary += f"  ✅ Strengths: {', '.join(self.primary_factors)}\n"
        if self.limiting_factors:
            summary += f"  ⚠️ Limitations: {', '.join(self.limiting_factors)}\n"
        
        return summary


@dataclass
class BeddingZoneCandidate:
    """
    Candidate bedding zone before final selection.
    
    Represents a potential bedding site identified during spatial search,
    with complete terrain and habitat characterization.
    """
    
    # Location
    lat: float
    lon: float
    distance_from_center_m: float  # Distance from search origin
    
    # Terrain metrics
    elevation_m: float
    slope_degrees: float
    aspect_degrees: float  # Downhill direction (0-360°)
    
    # Habitat quality
    canopy_coverage: float  # 0-1 (NDVI from Sentinel-2)
    food_availability: float  # 0-1 (mast crop density, browse availability)
    
    # Security factors
    road_distance_m: float  # Distance to nearest road (OSM)
    escape_routes: int = 0  # Number of viable escape routes
    
    # Scoring
    score_breakdown: Optional[BeddingScoreBreakdown] = None
    final_score: float = 0.0  # 0-100 composite score
    
    # Biological context
    zone_type: Optional[BeddingZoneType] = None
    biological_reasoning: str = ""
    
    def categorize_zone_type(self) -> BeddingZoneType:
        """
        Categorize bedding zone based on distance from search origin.
        
        Vermont Buck Bedding Patterns:
        - Primary (0-100m): Core bedding in thick cover, minimal movement
        - Secondary (100-250m): Alternate sites with escape routes
        - Escape (250-500m): Transition zones near feeding areas
        
        Returns:
            BeddingZoneType: Zone classification
        """
        if self.distance_from_center_m <= 100:
            return BeddingZoneType.PRIMARY
        elif self.distance_from_center_m <= 250:
            return BeddingZoneType.SECONDARY
        else:
            return BeddingZoneType.ESCAPE
    
    def meets_minimum_requirements(self) -> bool:
        """
        Check if candidate meets basic Vermont buck bedding criteria.
        
        Minimum Requirements:
        - Slope: 10-30° (optimal drainage and visibility)
        - Canopy: >60% coverage (security from aerial predators)
        - Road distance: >200m (human disturbance buffer)
        - Final score: >60 (biological viability threshold)
        
        Returns:
            bool: True if candidate meets all minimum criteria
        """
        return (
            10 <= self.slope_degrees <= 30 and
            self.canopy_coverage > 0.6 and
            self.road_distance_m > 200 and
            self.final_score > 60
        )


@dataclass
class BeddingZone:
    """
    Final selected bedding zone with complete characterization.
    
    Represents a high-quality bedding site selected from candidates,
    with GeoJSON export capability for frontend visualization.
    """
    
    # Location (WGS84)
    lat: float
    lon: float
    
    # Zone classification
    zone_type: BeddingZoneType
    rank: int  # 1 = highest quality, 2 = second-best, etc.
    
    # Terrain characterization
    elevation_m: float
    slope_degrees: float
    aspect_degrees: float  # Downhill direction
    uphill_direction: float  # Where deer faces (aspect + 180°)
    
    # Habitat quality
    canopy_coverage: float  # 0-1
    food_availability: float  # 0-1
    road_distance_m: float
    
    # Fields with defaults must come after fields without defaults
    dominant_vegetation: Optional[str] = None  # "hemlock", "oak-hickory", etc.
    escape_routes: List[Dict[str, Any]] = field(default_factory=list)  # Bearing and distance
    visibility_score: float = 0.0  # 0-100 based on uphill sightlines
    
    # Wind and thermal analysis
    thermal_wind_direction: Optional[float] = None  # Expected thermal draft bearing
    thermal_wind_strength: float = 0.0  # 0-1 strength multiplier
    scent_cone_safe: bool = True  # Whether upwind approaches are feasible
    
    # Scoring
    score_breakdown: BeddingScoreBreakdown = field(default_factory=BeddingScoreBreakdown)
    final_score: float = 0.0
    
    # Biological justification
    primary_reason: str = ""  # Top biological factor (e.g., "Perfect leeward shelter")
    ecological_context: str = ""  # Vermont-specific habitat notes
    
    # Distance from search origin
    distance_from_center_m: float = 0.0
    
    def to_geojson_feature(self) -> Dict[str, Any]:
        """
        Convert bedding zone to GeoJSON Feature for frontend mapping.
        
        Returns:
            Dict: GeoJSON Feature with point geometry and properties
        """
        return {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [self.lon, self.lat]
            },
            "properties": {
                "zone_type": self.zone_type.value,
                "rank": self.rank,
                "score": round(self.final_score, 1),
                "elevation_m": round(self.elevation_m, 1),
                "slope_deg": round(self.slope_degrees, 1),
                "aspect_deg": round(self.aspect_degrees, 0),
                "uphill_direction": round(self.uphill_direction, 0),
                "canopy_coverage": round(self.canopy_coverage * 100, 1),  # Convert to %
                "food_availability": round(self.food_availability * 100, 1),
                "road_distance_m": round(self.road_distance_m, 0),
                "distance_m": round(self.distance_from_center_m, 0),
                "thermal_direction": round(self.thermal_wind_direction, 0) if self.thermal_wind_direction else None,
                "primary_reason": self.primary_reason,
                "ecological_context": self.ecological_context,
            }
        }
    
    def get_aspect_classification(self) -> str:
        """
        Get cardinal direction for aspect (biological interpretation).
        
        Returns:
            str: 'north', 'east', 'south', or 'west' facing
        """
        aspect = self.aspect_degrees % 360
        
        if 315 <= aspect or aspect <= 45:
            return 'north'
        elif 45 < aspect <= 135:
            return 'east'
        elif 135 < aspect <= 225:
            return 'south'
        else:  # 225 < aspect < 315
            return 'west'
    
    def score_canopy(self, ndvi_value: float) -> float:
        """
        Score canopy coverage based on NDVI threshold.
        
        Vermont Buck Requirements:
        - >60% canopy for security (aerial predator protection)
        - Dense hemlock/hardwood mix preferred
        
        Args:
            ndvi_value: Normalized Difference Vegetation Index (0-1)
            
        Returns:
            float: Canopy score (0-100)
        """
        if ndvi_value >= 0.6:
            return 100
        elif ndvi_value >= 0.5:
            return 80
        elif ndvi_value >= 0.4:
            return 60
        else:
            return 40
