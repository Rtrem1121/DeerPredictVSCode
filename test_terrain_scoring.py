"""
Test terrain scoring to see if it's returning the same scores everywhere
"""
import sys
sys.path.insert(0, 'c:/Users/Rich/deer_pred_app')

from enhanced_bedding_zone_predictor import EnhancedBeddingZonePredictor

predictor = EnhancedBeddingZonePredictor()

# Manually call the terrain score function with different slopes/aspects
test_terrains = [
    (5, 180, 100, "Gentle south-facing"),
    (15, 180, 100, "Moderate south-facing"),
    (25, 180, 100, "Steep south-facing"),
    (15, 0, 100, "Moderate north-facing"),
    (15, 90, 100, "Moderate east-facing"),
    (15, 270, 100, "Moderate west-facing"),
]

weather_data = {
    'wind_direction': 180,
    'wind_speed': 5,
    'temperature': 50
}

print("Testing terrain scoring function:")
print("="*70)

scores = []
for slope, aspect, distance, desc in test_terrains:
    score = predictor._calculate_terrain_score(
        slope=slope,
        aspect=aspect,
        distance_m=distance,
        require_south_facing=False,
        max_slope_limit=30,
        weather_data=weather_data
    )
    scores.append(score)
    print(f"{desc:30s} Slope={slope:2.0f}° Aspect={aspect:3.0f}° → Score={score:.1f}%")

print("\n" + "="*70)
score_range = max(scores) - min(scores)
print(f"Score range: {min(scores):.1f}% to {max(scores):.1f}% (variation: {score_range:.1f}%)")

if score_range < 10:
    print("⚠️  WARNING: Terrain scores have very little variation!")
    print("   This means all candidates get similar scores, so selection may be arbitrary")
else:
    print("✅ Terrain scoring shows good variation")
