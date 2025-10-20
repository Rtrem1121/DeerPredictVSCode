"""
Stand Site Domain Models

Defines hunter stand positions with wind-aware crosswind logic (Phase 4.10).
Supports morning/evening/all-day stand calculations based on deer movement patterns.

References:
- Hirth (1977): Scent-based detection and upwind positioning
- Marchinton & Hirth (1984): Daily movement patterns and thermal drafts
- Vermont Fish & Wildlife: Hunting pressure and stand placement strategies
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from enum import Enum


class StandType(Enum):
    """Stand timing based on deer movement patterns."""
    MORNING = "morning"  # Deer returning to bedding (uphill movement)
    EVENING = "evening"  # Deer leaving for feeding (downhill movement)
    ALL_DAY = "all_day"  # Alternative position for wind shifts during rut


@dataclass
class ScentManagementResult:
    """
    Scent cone analysis for stand placement validation.
    
    Ensures hunter scent does NOT contaminate bedding zones,
    which would educate deer and render area un-huntable.
    """
    
    is_safe: bool  # True if scent does NOT blow into any bedding zone
    scent_bearing: float  # Direction scent travels (downwind from stand)
    violations: List[Dict[str, Any]] = field(default_factory=list)  # Zones contaminated
    
    # Wind details
    wind_direction: float = 0.0  # Wind FROM direction (degrees)
    wind_speed: float = 0.0  # mph
    
    # Thermal analysis
    thermal_active: bool = False  # Whether thermal drafts are significant
    thermal_direction: Optional[float] = None  # Upslope or downslope bearing
    
    # Validation details
    safe_approach_bearings: List[float] = field(default_factory=list)  # Bearings to access stand
    contamination_distance: Optional[float] = None  # Distance to nearest violation
    
    def get_summary(self) -> str:
        """Generate human-readable scent analysis summary."""
        if self.is_safe:
            summary = f"✅ SCENT SAFE: Downwind {self.scent_bearing:.0f}° clears all bedding zones"
            if self.thermal_active and self.thermal_direction:
                summary += f" (thermal: {self.thermal_direction:.0f}°)"
        else:
            summary = f"⚠️ SCENT VIOLATION: Wind {self.wind_direction:.0f}° at {self.wind_speed:.1f}mph "
            summary += f"contaminates {len(self.violations)} bedding zone(s)"
            if self.contamination_distance:
                summary += f" at {self.contamination_distance:.0f}m"
        
        return summary


@dataclass
class StandPosition:
    """
    Hunter stand location with biological justification.
    
    Phase 4.10 Wind-Aware Logic:
    - Wind >10 mph: Crosswind positioning (90° perpendicular to wind)
    - Wind <10 mph: Thermal/terrain positioning (uphill/downhill based on time)
    """
    
    # Location (WGS84)
    lat: float
    lon: float
    
    # Stand characteristics
    stand_type: StandType
    quality_score: float  # 0-100 composite score
    
    # Positioning logic
    bearing_from_bedding: float  # Direction from bedding zone to stand (degrees)
    distance_from_bedding_m: float  # Typical: 50-150m for crosswind intercept
    
    # Wind analysis (Phase 4.10)
    wind_aware: bool = False  # True if crosswind logic used (wind >10 mph)
    crosswind_bearing: Optional[float] = None  # 90° perpendicular to wind
    wind_direction: float = 0.0  # Wind FROM direction
    wind_speed: float = 0.0  # mph
    
    # Terrain positioning
    terrain_bearing: Optional[float] = None  # Uphill/downhill for thermal logic
    slope_degrees: float = 0.0
    elevation_m: float = 0.0
    
    # Scent management
    scent_result: Optional[ScentManagementResult] = None
    downwind_direction: float = 0.0  # Where scent blows (wind_direction + 180°)
    
    # Movement intercept
    expected_deer_bearing: Optional[float] = None  # Direction deer approach from
    intercept_angle: float = 0.0  # Angle between wind and deer movement (ideal: 90°)
    
    # Access planning
    approach_bearing: Optional[float] = None  # How hunter accesses stand
    approach_distance_m: float = 0.0
    approach_notes: str = ""  # E.g., "Use ridge to stay downwind"
    
    # Biological justification
    primary_reason: str = ""  # E.g., "Crosswind intercept of morning return"
    strategy_notes: str = ""  # Detailed tactical explanation
    
    def to_geojson_feature(self) -> Dict[str, Any]:
        """
        Convert stand position to GeoJSON Feature for frontend mapping.
        
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
                "stand_type": self.stand_type.value,
                "quality_score": round(self.quality_score, 1),
                "bearing": round(self.bearing_from_bedding, 0),
                "distance_m": round(self.distance_from_bedding_m, 0),
                "wind_aware": self.wind_aware,
                "wind_direction": round(self.wind_direction, 0),
                "wind_speed": round(self.wind_speed, 1),
                "crosswind_bearing": round(self.crosswind_bearing, 0) if self.crosswind_bearing else None,
                "terrain_bearing": round(self.terrain_bearing, 0) if self.terrain_bearing else None,
                "downwind_direction": round(self.downwind_direction, 0),
                "slope_deg": round(self.slope_degrees, 1),
                "scent_safe": self.scent_result.is_safe if self.scent_result else None,
                "primary_reason": self.primary_reason,
                "strategy_notes": self.strategy_notes,
                "approach_bearing": round(self.approach_bearing, 0) if self.approach_bearing else None,
            }
        }
    
    def validate_scent_management(self, bedding_zones: List[Any]) -> ScentManagementResult:
        """
        Validate that stand scent does NOT contaminate bedding zones.
        
        Critical for Vermont mature bucks - single scent intrusion can
        educate deer and make area un-huntable for weeks.
        
        Args:
            bedding_zones: List of BeddingZone objects to check
            
        Returns:
            ScentManagementResult: Validation outcome with violations
        """
        violations = []
        
        # Scent blows downwind (opposite of wind FROM direction)
        scent_bearing = (self.wind_direction + 180) % 360
        
        for zone in bedding_zones:
            # Calculate bearing from stand to bedding zone
            # (simplified - would use actual haversine in production)
            bearing_to_zone = self._calculate_bearing_to(zone.lat, zone.lon)
            
            # Check if zone is downwind (within 45° cone)
            angle_diff = abs((bearing_to_zone - scent_bearing + 180) % 360 - 180)
            
            if angle_diff <= 45:  # Zone is in downwind scent cone
                violations.append({
                    "zone_type": zone.zone_type.value,
                    "zone_rank": zone.rank,
                    "bearing_to_zone": bearing_to_zone,
                    "scent_bearing": scent_bearing,
                    "angle_diff": angle_diff,
                    "distance_m": self._calculate_distance_to(zone.lat, zone.lon),
                })
        
        return ScentManagementResult(
            is_safe=len(violations) == 0,
            scent_bearing=scent_bearing,
            violations=violations,
            wind_direction=self.wind_direction,
            wind_speed=self.wind_speed,
            contamination_distance=min([v["distance_m"] for v in violations]) if violations else None,
        )
    
    def _calculate_bearing_to(self, target_lat: float, target_lon: float) -> float:
        """
        Calculate bearing from stand to target location.
        
        Simplified calculation - production would use accurate haversine formula.
        
        Args:
            target_lat: Target latitude
            target_lon: Target longitude
            
        Returns:
            float: Bearing in degrees (0-360)
        """
        import math
        
        # Simplified bearing (accurate for small distances in Vermont)
        delta_lon = target_lon - self.lon
        delta_lat = target_lat - self.lat
        
        bearing_rad = math.atan2(delta_lon, delta_lat)
        bearing_deg = (math.degrees(bearing_rad) + 360) % 360
        
        return bearing_deg
    
    def _calculate_distance_to(self, target_lat: float, target_lon: float) -> float:
        """
        Calculate distance from stand to target (meters).
        
        Simplified calculation - production would use accurate haversine formula.
        
        Args:
            target_lat: Target latitude
            target_lon: Target longitude
            
        Returns:
            float: Distance in meters
        """
        import math
        
        # Simplified distance (accurate for small distances in Vermont)
        # 1 degree latitude ≈ 111,000 meters
        # 1 degree longitude ≈ 111,000 * cos(latitude) meters
        
        delta_lat = (target_lat - self.lat) * 111000
        delta_lon = (target_lon - self.lon) * 111000 * math.cos(math.radians(self.lat))
        
        distance = math.sqrt(delta_lat**2 + delta_lon**2)
        return distance
    
    def calculate_quality_score(self) -> float:
        """
        Calculate stand quality based on multiple factors.
        
        Scoring Components:
        - Scent management: 40% (critical - violations = 0 score)
        - Wind-aware positioning: 30% (crosswind intercept optimal)
        - Distance from bedding: 20% (50-150m ideal)
        - Terrain advantage: 10% (elevation, cover, access)
        
        Returns:
            float: Quality score (0-100)
        """
        if self.scent_result and not self.scent_result.is_safe:
            return 0  # Scent violation = unusable stand
        
        score = 0
        
        # Scent management (40 points)
        if self.scent_result and self.scent_result.is_safe:
            score += 40
        
        # Wind-aware positioning (30 points)
        if self.wind_aware and self.intercept_angle:
            # Ideal: 90° crosswind intercept
            angle_quality = 1 - (abs(90 - self.intercept_angle) / 90)
            score += 30 * angle_quality
        elif self.terrain_bearing:
            # Thermal logic fallback (less optimal)
            score += 20
        
        # Distance optimization (20 points)
        if 50 <= self.distance_from_bedding_m <= 150:
            score += 20
        elif self.distance_from_bedding_m < 50:
            score += 10  # Too close, may spook deer
        elif self.distance_from_bedding_m < 200:
            score += 15  # Acceptable range
        
        # Terrain advantage (10 points)
        if self.slope_degrees > 5:  # Some elevation advantage
            score += 5
        if self.approach_bearing:  # Planned access route
            score += 5
        
        return round(score, 1)
