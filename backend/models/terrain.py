"""
Terrain Domain Models

Handles LIDAR DEM extraction, slope/aspect computation, and terrain metrics
for Vermont whitetail deer bedding habitat analysis.

References:
- Nelson & Mech (1981): Thermal refugia and slope preferences
- Marchinton & Hirth (1984): Bedding behavior and terrain selection
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple, Any
import numpy as np
from scipy.ndimage import sobel
import logging

logger = logging.getLogger(__name__)


@dataclass
class TerrainMetrics:
    """
    Terrain characteristics for a single point.
    
    Vermont Whitetail Bedding Requirements:
    - Slope: 10-30° optimal (drainage + visibility)
    - Aspect: South-facing (cold weather) or leeward (windy conditions)
    - Benches: Micro-topography features providing escape routes
    """
    
    elevation_m: float
    slope_degrees: float
    aspect_degrees: float  # 0-360°, downhill direction (deer face uphill = aspect + 180°)
    
    # Micro-topography
    benches: List[Dict[str, Any]] = field(default_factory=list)
    ridges_nearby: bool = False
    
    # Terrain context
    roughness: float = 0.0  # Terrain variability (higher = more complex)
    curvature: float = 0.0  # Positive = convex (ridgetop), negative = concave (drainage)
    
    def is_bedding_viable(self) -> bool:
        """
        Check if terrain meets basic Vermont buck bedding criteria.
        
        Returns:
            bool: True if slope is in optimal range (10-30°)
        """
        return 10 <= self.slope_degrees <= 30
    
    def get_aspect_classification(self) -> str:
        """
        Classify aspect into cardinal directions for biological interpretation.
        
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
    
    def get_uphill_direction(self) -> float:
        """
        Calculate uphill direction (where deer typically faces when bedded).
        
        Returns:
            float: Bearing in degrees (0-360)
        """
        return (self.aspect_degrees + 180) % 360


@dataclass
class TerrainGrid:
    """
    Elevation grid for spatial terrain analysis.
    
    Used for extracting terrain metrics from LIDAR DEM data
    with rasterio (35cm resolution Vermont DEMs).
    """
    
    elevations: np.ndarray  # 2D array of elevation values (meters)
    resolution_m: float  # Cell size in meters (typically 0.35m for Vermont LIDAR)
    bounds: Tuple[float, float, float, float]  # (min_x, min_y, max_x, max_y) in meters
    center_lat: float
    center_lon: float
    
    def calculate_slope_aspect(self, row: int, col: int) -> Tuple[float, float]:
        """
        Calculate slope and aspect at a specific grid cell using Sobel operators.
        
        Args:
            row: Grid row index
            col: Grid column index
            
        Returns:
            Tuple[float, float]: (slope_degrees, aspect_degrees)
        """
        # Extract 3x3 window around target cell
        window = self.elevations[max(0, row-1):row+2, max(0, col-1):col+2]
        
        if window.shape[0] < 2 or window.shape[1] < 2:
            return 0.0, 0.0
        
        # Calculate gradients using Sobel filter
        grad_x = sobel(window, axis=1) / (8 * self.resolution_m)
        grad_y = sobel(window, axis=0) / (8 * self.resolution_m)
        
        # Slope: arctan of gradient magnitude
        slope_rad = np.arctan(np.sqrt(grad_x[1, 1]**2 + grad_y[1, 1]**2))
        slope_deg = np.degrees(slope_rad)
        
        # Aspect: direction of steepest descent (downhill)
        aspect_rad = np.arctan2(-grad_y[1, 1], grad_x[1, 1])
        aspect_deg = (90 - np.degrees(aspect_rad)) % 360
        
        return slope_deg, aspect_deg
    
    def extract_metrics(self, row: int, col: int) -> TerrainMetrics:
        """
        Extract complete terrain metrics for a grid cell.
        
        Args:
            row: Grid row index
            col: Grid column index
            
        Returns:
            TerrainMetrics: Complete terrain characterization
        """
        elevation = self.elevations[row, col]
        slope, aspect = self.calculate_slope_aspect(row, col)
        
        # Calculate terrain roughness (standard deviation of 5x5 window)
        window_size = 5
        r_start = max(0, row - window_size // 2)
        r_end = min(self.elevations.shape[0], row + window_size // 2 + 1)
        c_start = max(0, col - window_size // 2)
        c_end = min(self.elevations.shape[1], col + window_size // 2 + 1)
        
        window = self.elevations[r_start:r_end, c_start:c_end]
        roughness = float(np.std(window)) if window.size > 0 else 0.0
        
        return TerrainMetrics(
            elevation_m=float(elevation),
            slope_degrees=slope,
            aspect_degrees=aspect,
            roughness=roughness,
        )


class AspectCalculator:
    """
    Biological aspect scoring for Vermont whitetail deer bedding.
    
    Integrates wind direction, temperature, and terrain slope to score
    aspect quality based on deer thermoregulation and predator avoidance.
    
    References:
    - Nelson & Mech (1981): Deer thermoregulation in varying aspects
    - Hirth (1977): Wind-based predator detection strategies
    """
    
    @staticmethod
    def angular_diff(angle1: float, angle2: float) -> float:
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
    def score_aspect_biological(
        aspect: float,
        wind_direction: float,
        wind_speed: float,
        temperature: float,
        slope: float
    ) -> Tuple[float, str]:
        """
        Score aspect quality for bedding based on Vermont deer biology.
        
        Aspect Definition:
            - Aspect = Direction slope FACES (downhill direction)
            - Deer typically bed facing UPHILL (uphill = aspect + 180°)
            - Example: 180° aspect → slope faces south, deer faces north (uphill)
        
        Scoring Logic (Phase 4.7 Wind-Integrated):
            1. Wind >10 mph: LEEWARD SHELTER dominates (predator detection)
            2. Wind <10 mph: THERMAL ASPECT dominates (thermoregulation)
            3. Always: Uphill positioning preference (visibility + scent advantage)
        
        Args:
            aspect: Slope direction in degrees (0-360°, downhill)
            wind_direction: Wind FROM direction (degrees)
            wind_speed: Wind speed (mph)
            temperature: Air temperature (°F)
            slope: Terrain slope (degrees)
            
        Returns:
            Tuple[float, str]: (score 0-100, biological reasoning)
        """
        # Calculate leeward direction (sheltered side opposite wind)
        leeward_direction = (wind_direction + 180) % 360
        leeward_diff = AspectCalculator.angular_diff(aspect, leeward_direction)
        
        # PRIORITY 1: Wind >10 mph → LEEWARD SHELTER dominates
        if wind_speed > 10:
            if leeward_diff <= 30:  # Perfect leeward shelter
                score = 100
                reason = f"Perfect leeward shelter (aspect {aspect:.0f}° vs leeward {leeward_direction:.0f}°, wind {wind_speed:.1f}mph)"
            elif leeward_diff <= 60:  # Good leeward positioning
                score = 90
                reason = f"Good leeward shelter (aspect {aspect:.0f}° near leeward {leeward_direction:.0f}°, wind {wind_speed:.1f}mph)"
            elif leeward_diff <= 90:  # Moderate shelter (crosswind)
                score = 75
                reason = f"Moderate shelter (crosswind aspect {aspect:.0f}°, wind {wind_speed:.1f}mph)"
            else:  # Windward exposure
                windward_diff = AspectCalculator.angular_diff(aspect, wind_direction)
                if windward_diff <= 45:  # Direct windward exposure
                    score = 30
                    reason = f"⚠️ WINDWARD EXPOSURE (aspect {aspect:.0f}° faces wind {wind_direction:.0f}°, {wind_speed:.1f}mph)"
                else:
                    score = 50
                    reason = f"Partial wind exposure (aspect {aspect:.0f}°, wind {wind_speed:.1f}mph)"
            
            # Thermal bonus IF already leeward
            if leeward_diff <= 60:
                if temperature < 40 and 135 <= aspect <= 225:  # Cold + south-facing
                    score = min(100, score + 5)
                    reason += " + thermal bonus"
                elif temperature > 75 and (aspect <= 45 or aspect >= 315):  # Hot + north-facing
                    score = min(100, score + 5)
                    reason += " + cooling bonus"
        
        # PRIORITY 2: Wind <10 mph → THERMAL ASPECT dominates
        else:
            if temperature < 40:  # Cold weather
                if 135 <= aspect <= 225:  # South-facing
                    score = 100
                    reason = f"Thermal optimal (south-facing {aspect:.0f}° for cold weather {temperature:.1f}°F)"
                elif 90 <= aspect <= 270:  # East to west arc (some sun)
                    score = 80
                    reason = f"Thermal acceptable (aspect {aspect:.0f}°, cold weather {temperature:.1f}°F)"
                else:  # North-facing in cold
                    score = 50
                    reason = f"⚠️ North-facing {aspect:.0f}° in cold weather {temperature:.1f}°F (needs dense canopy)"
            
            elif temperature > 75:  # Hot weather
                if aspect <= 45 or aspect >= 315:  # North-facing
                    score = 100
                    reason = f"Thermal optimal (north-facing {aspect:.0f}° for hot weather {temperature:.1f}°F)"
                elif 270 <= aspect <= 360 or 0 <= aspect <= 90:  # North to east arc (shade)
                    score = 80
                    reason = f"Thermal acceptable (aspect {aspect:.0f}°, hot weather {temperature:.1f}°F)"
                else:  # South-facing in heat
                    score = 50
                    reason = f"⚠️ South-facing {aspect:.0f}° in hot weather {temperature:.1f}°F (needs heavy canopy)"
            
            else:  # Moderate temperature (40-75°F)
                if 135 <= aspect <= 225:  # South-facing
                    score = 90
                    reason = f"Thermal good (south-facing {aspect:.0f}°, moderate {temperature:.1f}°F)"
                else:
                    score = 85
                    reason = f"Thermal neutral (aspect {aspect:.0f}°, moderate {temperature:.1f}°F)"
            
            # Light wind leeward bonus
            if wind_speed > 0 and leeward_diff <= 45:
                score = min(100, score + 5)
                reason += f" + light leeward bonus (wind {wind_speed:.1f}mph)"
        
        # PRIORITY 3: Slope penalties and bonuses
        if slope > 30:
            penalty = min(20, (slope - 30) * 2)  # 2 points per degree over 30°
            score -= penalty
            reason += f" - steep slope penalty ({slope:.1f}°)"
        
        if 10 <= slope <= 25:
            score = min(100, score + 5)
            reason += " + ideal slope range"
        
        return (max(0, min(100, score)), reason)
