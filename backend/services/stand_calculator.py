"""
Wind-Aware Stand Calculator Service

Implements Phase 4.10 crosswind stand positioning for Vermont whitetail deer hunting.
Extracted from enhanced_bedding_zone_predictor.py (lines 2573-2803) to reduce bloat.

Stand Positioning Logic:
1. Wind >10 mph: CROSSWIND positioning (90° perpendicular to wind)
   - Evening: Crosswind option closest to downhill (deer feeding movement)
   - Morning: Crosswind option closest to uphill (deer return to bedding)
   - All-day: Opposite crosswind from morning (coverage diversity)

2. Wind <10 mph: TERRAIN/THERMAL positioning
   - Evening: Thermal downslope + deer movement
   - Morning: Uphill intercept (deer destination)
   - All-day: Alternate approach angle

References:
- Hirth (1977): Scent-based detection and upwind positioning
- Marchinton & Hirth (1984): Daily movement patterns and thermal drafts
- Vermont Fish & Wildlife: Stand placement and hunting pressure

Author: Extracted from God Object refactoring
Date: October 19, 2025
"""

from typing import Dict, Tuple, Optional, List, Any
from dataclasses import dataclass
import math
import logging

logger = logging.getLogger(__name__)


@dataclass
class ThermalWindData:
    """Thermal draft characteristics for stand positioning."""
    direction: float  # Bearing in degrees (0-360)
    strength: float  # 0-1 multiplier
    phase: str = "unknown"  # Thermal phase: "strong_evening_downslope", "peak_morning_upslope", etc.
    is_active: bool = False  # Whether thermal is significant enough to influence scent


@dataclass
class StandCalculationResult:
    """Result of stand position calculation with biological justification."""
    bearing: float  # Direction from bedding zone to stand (degrees)
    distance_m: float  # Distance from bedding zone (meters)
    
    # Wind awareness
    wind_aware: bool  # True if crosswind logic used
    crosswind_bearing: Optional[float] = None  # Crosswind bearing (if wind >10 mph)
    
    # Scent management
    scent_safe: bool = True
    scent_bearing: float = 0.0  # Direction scent travels
    
    # Biological reasoning
    strategy: str = ""  # "crosswind", "thermal", "terrain", "deer_movement"
    primary_reason: str = ""
    adjustments: List[str] = None
    
    def __post_init__(self):
        if self.adjustments is None:
            self.adjustments = []


class WindAwareStandCalculator:
    """
    Calculate optimal hunter stand positions using Phase 4.10 wind-aware logic.
    
    This service extracts stand positioning from the main predictor to enable:
    - Unit testing with mock weather/terrain data
    - Reuse across different prediction contexts
    - Biological validation against Vermont deer movement patterns
    """
    
    # Constants for stand positioning
    WIND_THRESHOLD_MPH = 10.0  # Above this: crosswind logic; below: terrain logic
    STRONG_WIND_MPH = 20.0  # Wind overrides even active thermals
    CROSSWIND_ANGLE = 90.0  # Perpendicular to wind direction
    
    # Distance multipliers
    EVENING_BASE_MULTIPLIER = 1.5  # Evening stand distance factor
    MORNING_BASE_MULTIPLIER = 1.3  # Morning stand distance factor
    ALLDAY_BASE_MULTIPLIER = 1.0  # All-day stand distance factor
    
    def __init__(self):
        """Initialize stand calculator."""
        pass
    
    @staticmethod
    def _angular_diff(angle1: float, angle2: float) -> float:
        """
        Calculate smallest angle between two bearings (handles 0°/360° wrap).
        
        Args:
            angle1: First bearing (degrees)
            angle2: Second bearing (degrees)
            
        Returns:
            float: Smallest angle difference (0-180°)
        """
        diff = abs(angle1 - angle2)
        return min(diff, 360 - diff)
    
    @staticmethod
    def _combine_bearings(bearing1: float, bearing2: float, 
                         weight1: float, weight2: float) -> float:
        """
        Combine two bearings using weighted vector averaging.
        
        Handles 0°/360° wrap-around correctly by converting to vectors.
        
        Args:
            bearing1: First bearing (degrees)
            bearing2: Second bearing (degrees)
            weight1: Weight for bearing1 (0-1)
            weight2: Weight for bearing2 (0-1)
            
        Returns:
            float: Combined bearing (degrees, 0-360)
        """
        # Convert bearings to unit vectors
        rad1 = math.radians(bearing1)
        rad2 = math.radians(bearing2)
        
        x = weight1 * math.sin(rad1) + weight2 * math.sin(rad2)
        y = weight1 * math.cos(rad1) + weight2 * math.cos(rad2)
        
        # Convert back to bearing
        combined_rad = math.atan2(x, y)
        combined_deg = (math.degrees(combined_rad) + 360) % 360
        
        return combined_deg
    
    def calculate_evening_stand(
        self,
        wind_direction: float,
        wind_speed_mph: float,
        downhill_direction: float,
        downwind_direction: float,
        thermal_data: Optional[ThermalWindData],
        slope: float
    ) -> StandCalculationResult:
        """
        Calculate evening stand position.
        
        Evening Strategy:
        - Deer move DOWNHILL from bedding to feeding areas
        - Wind >10 mph: Crosswind intercept near downhill movement
        - Wind <10 mph: Thermal downslope + deer movement combination
        
        Args:
            wind_direction: Wind FROM direction (degrees)
            wind_speed_mph: Wind speed (mph)
            downhill_direction: Slope faces this direction (degrees)
            downwind_direction: Direction downwind (wind_direction + 180°)
            thermal_data: Thermal draft information
            slope: Terrain slope (degrees)
            
        Returns:
            StandCalculationResult: Evening stand position and reasoning
        """
        adjustments = []
        
        # PHASE 4.10: Wind >10 mph uses CROSSWIND positioning
        if wind_speed_mph > self.WIND_THRESHOLD_MPH:
            # Calculate crosswind options (90° perpendicular to wind)
            crosswind_right = (wind_direction + self.CROSSWIND_ANGLE) % 360
            crosswind_left = (wind_direction - self.CROSSWIND_ANGLE) % 360
            
            # Choose crosswind option closest to downhill (deer movement)
            diff_right = self._angular_diff(crosswind_right, downhill_direction)
            diff_left = self._angular_diff(crosswind_left, downhill_direction)
            
            if diff_right < diff_left:
                bearing = crosswind_right
                strategy = f"Crosswind RIGHT (wind {wind_speed_mph:.1f}mph, downhill {downhill_direction:.0f}°)"
            else:
                bearing = crosswind_left
                strategy = f"Crosswind LEFT (wind {wind_speed_mph:.1f}mph, downhill {downhill_direction:.0f}°)"
            
            logger.info(
                f"🌬️ WIND-AWARE EVENING: Crosswind bearing={bearing:.0f}° "
                f"(wind {wind_direction:.0f}° at {wind_speed_mph:.1f}mph, "
                f"downhill {downhill_direction:.0f}°)"
            )
            
            result = StandCalculationResult(
                bearing=bearing,
                distance_m=0,  # Will be calculated by caller
                wind_aware=True,
                crosswind_bearing=bearing,
                strategy="crosswind",
                primary_reason=strategy,
                adjustments=adjustments
            )
            
        else:  # LIGHT WIND: Use thermal/terrain logic
            # Check if thermal is active
            thermal_active = (
                thermal_data is not None and (
                    thermal_data.phase in ["strong_evening_downslope", "peak_evening_downslope", 
                                          "post_sunset_maximum"] or
                    thermal_data.strength > 0.05
                )
            )
            
            if thermal_active and wind_speed_mph < self.STRONG_WIND_MPH:
                # THERMAL DOMINATES: Combine thermal + deer movement
                bearing = self._combine_bearings(
                    thermal_data.direction,  # Thermal flows downhill
                    downhill_direction,      # Deer move downhill
                    0.6,  # Thermal weight
                    0.4   # Deer movement weight
                )
                
                # Add prevailing wind influence based on speed
                if wind_speed_mph < 5:
                    wind_weight = 0.0
                elif wind_speed_mph < 10:
                    wind_weight = 0.05
                else:
                    wind_weight = 0.15
                
                bearing = self._combine_bearings(
                    bearing,
                    downwind_direction,
                    1.0 - wind_weight,
                    wind_weight
                )
                
                strategy = f"Thermal dominant (phase={thermal_data.phase}, wind_weight={wind_weight:.0%})"
                logger.info(
                    f"🌅 THERMAL DOMINANT: Evening bearing={bearing:.0f}°, "
                    f"Wind speed={wind_speed_mph:.1f}mph, Wind weight={wind_weight:.0%}, "
                    f"Thermal phase={thermal_data.phase}"
                )
                
            elif wind_speed_mph >= self.STRONG_WIND_MPH:
                # STRONG WIND OVERRIDES THERMAL
                bearing = self._combine_bearings(
                    downhill_direction,  # Deer movement
                    downwind_direction,  # Prevailing wind
                    0.4,  # Deer movement
                    0.6   # Wind dominates
                )
                
                strategy = f"Wind dominant (>20mph overrides thermal)"
                logger.info(
                    f"💨 WIND DOMINANT: Evening bearing={bearing:.0f}°, "
                    f"Wind speed={wind_speed_mph:.1f}mph (>20mph overrides thermal)"
                )
                
            else:
                # NO THERMAL, WEAK WIND: Deer movement + scaled wind
                wind_weight = min(0.4, wind_speed_mph / 50)
                bearing = self._combine_bearings(
                    downhill_direction,
                    downwind_direction,
                    1.0 - wind_weight,
                    wind_weight
                )
                
                strategy = f"Deer movement (wind_weight={wind_weight:.0%})"
                logger.info(
                    f"🦌 DEER MOVEMENT: Evening bearing={bearing:.0f}°, "
                    f"Wind speed={wind_speed_mph:.1f}mph, Wind weight={wind_weight:.0%}"
                )
            
            result = StandCalculationResult(
                bearing=bearing,
                distance_m=0,
                wind_aware=False,
                strategy="thermal" if thermal_active else "deer_movement",
                primary_reason=strategy,
                adjustments=adjustments
            )
        
        return result
    
    def calculate_morning_stand(
        self,
        wind_direction: float,
        wind_speed_mph: float,
        uphill_direction: float,
        downwind_direction: float,
        thermal_data: Optional[ThermalWindData],
        slope: float
    ) -> StandCalculationResult:
        """
        Calculate morning stand position.
        
        Morning Strategy:
        - Deer move UPHILL from feeding back to bedding
        - Wind >10 mph: Crosswind intercept near uphill destination
        - Wind <10 mph: Uphill intercept (on slopes) or wind-based (flat terrain)
        
        Args:
            wind_direction: Wind FROM direction (degrees)
            wind_speed_mph: Wind speed (mph)
            uphill_direction: Opposite of slope direction (degrees)
            downwind_direction: Direction downwind (wind_direction + 180°)
            thermal_data: Thermal draft information
            slope: Terrain slope (degrees)
            
        Returns:
            StandCalculationResult: Morning stand position and reasoning
        """
        adjustments = []
        
        # PHASE 4.10: Wind >10 mph uses CROSSWIND positioning
        if wind_speed_mph > self.WIND_THRESHOLD_MPH:
            # Calculate crosswind options
            crosswind_right = (wind_direction + self.CROSSWIND_ANGLE) % 360
            crosswind_left = (wind_direction - self.CROSSWIND_ANGLE) % 360
            
            if slope > 5:  # Sloped terrain
                # Prefer crosswind option closer to uphill (deer destination)
                diff_right = self._angular_diff(crosswind_right, uphill_direction)
                diff_left = self._angular_diff(crosswind_left, uphill_direction)
                
                bearing = crosswind_right if diff_right < diff_left else crosswind_left
                strategy = f"Crosswind (wind {wind_speed_mph:.1f}mph, slope {slope:.1f}°, uphill {uphill_direction:.0f}°)"
                
                logger.info(
                    f"🌬️ WIND-AWARE MORNING: Crosswind bearing={bearing:.0f}° "
                    f"(wind {wind_direction:.0f}° at {wind_speed_mph:.1f}mph, "
                    f"slope {slope:.1f}°, uphill {uphill_direction:.0f}°)"
                )
            else:  # Flat terrain
                bearing = crosswind_right  # Default to right crosswind
                strategy = f"Crosswind (wind {wind_speed_mph:.1f}mph, flat terrain)"
                
                logger.info(
                    f"🌬️ WIND-AWARE MORNING: Crosswind bearing={bearing:.0f}° "
                    f"(wind {wind_direction:.0f}° at {wind_speed_mph:.1f}mph, flat terrain)"
                )
            
            result = StandCalculationResult(
                bearing=bearing,
                distance_m=0,
                wind_aware=True,
                crosswind_bearing=bearing,
                strategy="crosswind",
                primary_reason=strategy,
                adjustments=adjustments
            )
            
        else:  # LIGHT WIND: Use terrain/thermal logic
            if slope > 5:  # Sloped terrain
                if thermal_data is not None and thermal_data.strength > 0.3:  # Strong upslope thermal
                    # Combine uphill with slight crosswind offset
                    bearing = self._combine_bearings(
                        uphill_direction,
                        (uphill_direction + 30) % 360,  # Crosswind variation
                        0.8,  # Primarily uphill
                        0.2   # Minor crosswind
                    )
                    strategy = f"Uphill with crosswind offset (slope {slope:.1f}°)"
                    logger.info(
                        f"🌅 MORNING STAND: Uphill ({uphill_direction:.0f}°) "
                        f"with crosswind offset on {slope:.1f}° slope"
                    )
                else:
                    # Pure uphill positioning
                    bearing = uphill_direction
                    strategy = f"Uphill intercept (slope {slope:.1f}°)"
                    logger.info(
                        f"🏔️ MORNING STAND: Uphill intercept ({uphill_direction:.0f}°) "
                        f"on {slope:.1f}° slope"
                    )
            else:  # Flat terrain
                # Use wind-based positioning
                bearing = self._combine_bearings(
                    downwind_direction,
                    (wind_direction + 90) % 360,  # Crosswind
                    0.7, 0.3
                )
                strategy = "Wind-based (flat terrain)"
                logger.info(
                    f"🌲 MORNING STAND: Wind-based ({bearing:.0f}°) on flat terrain"
                )
            
            result = StandCalculationResult(
                bearing=bearing,
                distance_m=0,
                wind_aware=False,
                strategy="terrain" if slope > 5 else "wind_based",
                primary_reason=strategy,
                adjustments=adjustments
            )
        
        return result
    
    def calculate_allday_stand(
        self,
        wind_direction: float,
        wind_speed_mph: float,
        morning_bearing: float,
        uphill_direction: float,
        downwind_direction: float,
        slope: float
    ) -> StandCalculationResult:
        """
        Calculate all-day/alternate stand position.
        
        All-Day Strategy:
        - Provides alternative approach for wind shifts or midday hunting
        - Wind >10 mph: OPPOSITE crosswind from morning (coverage diversity)
        - Wind <10 mph: Alternate uphill angle or wind-based
        
        Args:
            wind_direction: Wind FROM direction (degrees)
            wind_speed_mph: Wind speed (mph)
            morning_bearing: Morning stand bearing (to avoid duplication)
            uphill_direction: Opposite of slope direction (degrees)
            downwind_direction: Direction downwind (wind_direction + 180°)
            slope: Terrain slope (degrees)
            
        Returns:
            StandCalculationResult: All-day stand position and reasoning
        """
        adjustments = []
        
        # PHASE 4.10: Wind >10 mph uses OPPOSITE crosswind from morning
        if wind_speed_mph > self.WIND_THRESHOLD_MPH:
            # Calculate crosswind options
            crosswind_right = (wind_direction + self.CROSSWIND_ANGLE) % 360
            crosswind_left = (wind_direction - self.CROSSWIND_ANGLE) % 360
            
            # Determine which crosswind morning used
            diff_to_right = self._angular_diff(morning_bearing, crosswind_right)
            diff_to_left = self._angular_diff(morning_bearing, crosswind_left)
            
            # Use opposite crosswind for diversity
            if diff_to_right < diff_to_left:
                bearing = crosswind_left  # Morning used right, so use left
            else:
                bearing = crosswind_right  # Morning used left, so use right
            
            strategy = f"Alternate crosswind (opposite from morning {morning_bearing:.0f}°)"
            logger.info(
                f"🌬️ WIND-AWARE ALL-DAY: Alternate crosswind bearing={bearing:.0f}° "
                f"(wind {wind_direction:.0f}° at {wind_speed_mph:.1f}mph, "
                f"opposite from morning {morning_bearing:.0f}°)"
            )
            
            result = StandCalculationResult(
                bearing=bearing,
                distance_m=0,
                wind_aware=True,
                crosswind_bearing=bearing,
                strategy="crosswind_alternate",
                primary_reason=strategy,
                adjustments=adjustments
            )
            
        else:  # LIGHT WIND: Use terrain/thermal logic
            if slope > 5:  # Sloped terrain
                # Alternate uphill approach
                bearing = (uphill_direction + 45) % 360
                strategy = f"Uphill variation (slope {slope:.1f}°)"
                logger.info(
                    f"🏔️ ALTERNATE STAND: Uphill variation ({bearing:.0f}°) "
                    f"on {slope:.1f}° slope"
                )
            else:  # Flat terrain
                if slope > 15:
                    # Crosswind funnel on steep terrain
                    bearing = (downwind_direction + 45) % 360
                    strategy = "Crosswind funnel (steep terrain)"
                else:
                    # Pure downwind on flat terrain
                    bearing = downwind_direction
                    strategy = "Wind-based (flat terrain)"
                
                logger.info(
                    f"💨 ALTERNATE STAND: {strategy} ({bearing:.0f}°)"
                )
            
            result = StandCalculationResult(
                bearing=bearing,
                distance_m=0,
                wind_aware=False,
                strategy="terrain_alternate" if slope > 5 else "wind_based",
                primary_reason=strategy,
                adjustments=adjustments
            )
        
        return result
    
    def validate_scent_management(
        self,
        stand_bearing: float,
        wind_direction: float,
        wind_speed_mph: float,
        bedding_zones: List[Dict[str, Any]]
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate that stand scent does NOT contaminate bedding zones.
        
        Critical for Vermont mature bucks - single scent intrusion can
        educate deer and make area un-huntable for weeks.
        
        Args:
            stand_bearing: Direction from bedding to stand (degrees)
            wind_direction: Wind FROM direction (degrees)
            wind_speed_mph: Wind speed (mph)
            bedding_zones: List of bedding zone dictionaries with lat/lon
            
        Returns:
            Tuple[bool, List[Dict]]: (is_safe, list of violations)
        """
        scent_bearing = (wind_direction + 180) % 360  # Scent blows downwind
        violations = []
        
        # Simplified scent cone check (would use actual bearing calculations in production)
        for zone in bedding_zones:
            # Check if zone is downwind (within 45° cone)
            angle_diff = self._angular_diff(stand_bearing, scent_bearing)
            
            if angle_diff <= 45:  # Zone is in downwind scent cone
                violations.append({
                    "zone_type": zone.get("zone_type", "unknown"),
                    "bearing_to_zone": stand_bearing,
                    "scent_bearing": scent_bearing,
                    "angle_diff": angle_diff,
                })
        
        is_safe = len(violations) == 0
        
        if not is_safe:
            logger.warning(
                f"⚠️ SCENT VIOLATION: Wind {wind_direction:.0f}° at {wind_speed_mph:.1f}mph "
                f"contaminates {len(violations)} bedding zone(s)"
            )
        
        return is_safe, violations
