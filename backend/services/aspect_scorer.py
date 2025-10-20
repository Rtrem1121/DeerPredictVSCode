"""
Biological Aspect Scoring Service

Implements Phase 4.7 wind-integrated aspect scoring for Vermont whitetail deer.
Extracted from enhanced_bedding_zone_predictor.py (lines 2023-2153) to reduce bloat.

Scoring Logic:
1. Wind >10 mph: LEEWARD SHELTER dominates (predator detection via scent)
2. Wind <10 mph: THERMAL ASPECT dominates (thermoregulation)
3. Always: Uphill positioning preference (visibility + scent advantage)

References:
- Nelson & Mech (1981): Deer thermoregulation in varying aspects and weather
- Hirth (1977): Wind-based predator detection strategies
- Marchinton & Hirth (1984): Bedding site selection and thermal refugia

Author: Extracted from God Object refactoring (Phase 4.10 cleanup)
Date: October 19, 2025
"""

from typing import Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)


class BiologicalAspectScorer:
    """
    Vermont whitetail buck aspect preferences based on wind and thermal biology.
    
    This class isolates the complex aspect scoring logic that previously lived
    in the main predictor file, enabling:
    - Unit testing with mock weather data
    - Reuse across bedding and stand placement
    - Biological validation against Vermont deer studies
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
    
    def score_aspect(
        self,
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
        
        Biological Priorities:
            1. Wind >10 mph: Leeward shelter for scent-based predator detection
            2. Wind <10 mph: Thermal comfort (south-facing cold, north-facing hot)
            3. Always: Slope 10-30° optimal (drainage + visibility + comfort)
        
        Args:
            aspect: Slope direction in degrees (0-360°, downhill)
            wind_direction: Wind FROM direction (degrees)
            wind_speed: Wind speed (mph)
            temperature: Air temperature (°F)
            slope: Terrain slope (degrees)
            
        Returns:
            Tuple[float, str]: (score 0-100, biological reasoning)
            
        Examples:
            >>> scorer = BiologicalAspectScorer()
            >>> # East wind (83°), SSW aspect (206°), strong wind
            >>> score, reason = scorer.score_aspect(206, 83, 12.8, 45, 16)
            >>> assert score >= 90  # Good leeward shelter
            >>> assert "leeward" in reason.lower()
        """
        # Calculate leeward direction (sheltered side opposite wind)
        leeward_direction = (wind_direction + 180) % 360
        leeward_diff = self.angular_diff(aspect, leeward_direction)
        
        # PRIORITY 1: Wind >10 mph → LEEWARD SHELTER dominates
        if wind_speed > 10:
            score, reason = self._score_leeward_shelter(
                aspect, wind_direction, wind_speed, leeward_direction, leeward_diff
            )
            
            # Thermal bonus IF already leeward
            if leeward_diff <= 60:
                bonus, bonus_reason = self._apply_thermal_bonus(aspect, temperature)
                score = min(100, score + bonus)
                if bonus > 0:
                    reason += bonus_reason
        
        # PRIORITY 2: Wind <10 mph → THERMAL ASPECT dominates
        else:
            score, reason = self._score_thermal_comfort(aspect, temperature)
            
            # Light wind leeward bonus
            if wind_speed > 0 and leeward_diff <= 45:
                score = min(100, score + 5)
                reason += f" + light leeward bonus (wind {wind_speed:.1f}mph)"
        
        # PRIORITY 3: Slope penalties and bonuses
        score, reason = self._apply_slope_adjustments(score, reason, slope)
        
        return (max(0, min(100, score)), reason)
    
    def _score_leeward_shelter(
        self,
        aspect: float,
        wind_direction: float,
        wind_speed: float,
        leeward_direction: float,
        leeward_diff: float
    ) -> Tuple[float, str]:
        """
        Score aspect based on leeward shelter quality (wind >10 mph).
        
        Deer prioritize leeward positioning to use wind for predator detection
        while avoiding wind chill and scent contamination from upwind threats.
        
        Args:
            aspect: Slope direction (degrees)
            wind_direction: Wind FROM direction (degrees)
            wind_speed: Wind speed (mph)
            leeward_direction: Sheltered direction (wind_direction + 180°)
            leeward_diff: Angular difference between aspect and leeward
            
        Returns:
            Tuple[float, str]: (score, reasoning)
        """
        if leeward_diff <= 30:  # Perfect leeward shelter
            score = 100
            reason = (
                f"Perfect leeward shelter (aspect {aspect:.0f}° vs leeward "
                f"{leeward_direction:.0f}°, wind {wind_speed:.1f}mph)"
            )
        
        elif leeward_diff <= 60:  # Good leeward positioning
            score = 90
            reason = (
                f"Good leeward shelter (aspect {aspect:.0f}° near leeward "
                f"{leeward_direction:.0f}°, wind {wind_speed:.1f}mph)"
            )
        
        elif leeward_diff <= 90:  # Moderate shelter (crosswind)
            score = 75
            reason = f"Moderate shelter (crosswind aspect {aspect:.0f}°, wind {wind_speed:.1f}mph)"
        
        else:  # Windward exposure (within 90° of wind direction)
            windward_diff = self.angular_diff(aspect, wind_direction)
            if windward_diff <= 45:  # Direct windward exposure
                score = 30
                reason = (
                    f"⚠️ WINDWARD EXPOSURE (aspect {aspect:.0f}° faces wind "
                    f"{wind_direction:.0f}°, {wind_speed:.1f}mph)"
                )
            else:
                score = 50
                reason = f"Partial wind exposure (aspect {aspect:.0f}°, wind {wind_speed:.1f}mph)"
        
        return score, reason
    
    def _apply_thermal_bonus(self, aspect: float, temperature: float) -> Tuple[float, str]:
        """
        Apply thermal aspect bonus when leeward shelter already present.
        
        Args:
            aspect: Slope direction (degrees)
            temperature: Air temperature (°F)
            
        Returns:
            Tuple[float, str]: (bonus points, bonus reasoning)
        """
        if temperature < 40 and 135 <= aspect <= 225:  # Cold + south-facing
            return 5, " + thermal bonus"
        elif temperature > 75 and (aspect <= 45 or aspect >= 315):  # Hot + north-facing
            return 5, " + cooling bonus"
        else:
            return 0, ""
    
    def _score_thermal_comfort(self, aspect: float, temperature: float) -> Tuple[float, str]:
        """
        Score aspect based on thermal comfort (wind <10 mph).
        
        Deer thermoregulation strategies (Nelson & Mech 1981):
        - Cold (<40°F): South-facing slopes for solar warming
        - Hot (>75°F): North-facing slopes for shade cooling
        - Moderate (40-75°F): All aspects acceptable, slight south preference
        
        Args:
            aspect: Slope direction (degrees)
            temperature: Air temperature (°F)
            
        Returns:
            Tuple[float, str]: (score, reasoning)
        """
        if temperature < 40:  # Cold weather
            if 135 <= aspect <= 225:  # South-facing
                score = 100
                reason = (
                    f"Thermal optimal (south-facing {aspect:.0f}° for cold "
                    f"weather {temperature:.1f}°F)"
                )
            elif 90 <= aspect <= 270:  # East to west arc (some sun)
                score = 80
                reason = f"Thermal acceptable (aspect {aspect:.0f}°, cold weather {temperature:.1f}°F)"
            else:  # North-facing in cold
                score = 50
                reason = (
                    f"⚠️ North-facing {aspect:.0f}° in cold weather {temperature:.1f}°F "
                    f"(needs dense canopy)"
                )
        
        elif temperature > 75:  # Hot weather
            if aspect <= 45 or aspect >= 315:  # North-facing
                score = 100
                reason = (
                    f"Thermal optimal (north-facing {aspect:.0f}° for hot "
                    f"weather {temperature:.1f}°F)"
                )
            elif 270 <= aspect <= 360 or 0 <= aspect <= 90:  # North to east arc (shade)
                score = 80
                reason = f"Thermal acceptable (aspect {aspect:.0f}°, hot weather {temperature:.1f}°F)"
            else:  # South-facing in heat
                score = 50
                reason = (
                    f"⚠️ South-facing {aspect:.0f}° in hot weather {temperature:.1f}°F "
                    f"(needs heavy canopy)"
                )
        
        else:  # Moderate temperature (40-75°F)
            if 135 <= aspect <= 225:  # South-facing
                score = 90
                reason = f"Thermal good (south-facing {aspect:.0f}°, moderate {temperature:.1f}°F)"
            else:
                score = 85
                reason = f"Thermal neutral (aspect {aspect:.0f}°, moderate {temperature:.1f}°F)"
        
        return score, reason
    
    def _apply_slope_adjustments(
        self, score: float, reason: str, slope: float
    ) -> Tuple[float, str]:
        """
        Apply slope-based penalties and bonuses to aspect score.
        
        Vermont Buck Preferences:
        - Optimal: 10-30° (drainage, visibility, bedding comfort)
        - Penalty: >30° (too steep for comfortable bedding)
        - Bonus: 10-25° (ideal range)
        
        Args:
            score: Current aspect score
            reason: Current reasoning
            slope: Terrain slope (degrees)
            
        Returns:
            Tuple[float, str]: (adjusted score, updated reasoning)
        """
        if slope > 30:
            penalty = min(20, (slope - 30) * 2)  # 2 points per degree over 30°
            score -= penalty
            reason += f" - steep slope penalty ({slope:.1f}°)"
        
        if 10 <= slope <= 25:
            score = min(100, score + 5)
            reason += " + ideal slope range"
        
        return score, reason
    
    def validate_score(
        self,
        aspect: float,
        wind_direction: float,
        wind_speed: float,
        temperature: float,
        slope: float,
        expected_min_score: float = 60
    ) -> Dict[str, Any]:
        """
        Validate aspect scoring against biological expectations.
        
        Useful for testing and debugging to ensure scoring aligns with
        Vermont deer behavior observations.
        
        Args:
            aspect: Slope direction (degrees)
            wind_direction: Wind FROM direction (degrees)
            wind_speed: Wind speed (mph)
            temperature: Air temperature (°F)
            slope: Terrain slope (degrees)
            expected_min_score: Minimum acceptable score
            
        Returns:
            Dict with score, reasoning, and validation status
        """
        score, reason = self.score_aspect(aspect, wind_direction, wind_speed, temperature, slope)
        
        leeward_direction = (wind_direction + 180) % 360
        leeward_diff = self.angular_diff(aspect, leeward_direction)
        
        validation = {
            "score": score,
            "reasoning": reason,
            "passed": score >= expected_min_score,
            "aspect": aspect,
            "wind_direction": wind_direction,
            "wind_speed": wind_speed,
            "temperature": temperature,
            "slope": slope,
            "leeward_direction": leeward_direction,
            "leeward_diff": leeward_diff,
            "priority_mode": "leeward_shelter" if wind_speed > 10 else "thermal_comfort",
        }
        
        return validation
