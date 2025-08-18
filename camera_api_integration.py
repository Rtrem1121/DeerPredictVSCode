#!/usr/bin/env python3
"""
Buck Camera Placement API Integration
Adds single optimal camera placement to existing endpoints
"""
from fastapi import APIRouter, Query
from advanced_camera_placement import BuckCameraPlacement
import logging

logger = logging.getLogger(__name__)

# Create a new router for camera placement
camera_router = APIRouter(prefix="/api/camera", tags=["Trail Camera"])

# Initialize the camera placement system
camera_system = BuckCameraPlacement()

@camera_router.get("/optimal-placement")
async def get_optimal_camera_placement(
    lat: float = Query(..., description="Target latitude"),
    lon: float = Query(..., description="Target longitude")
):
    """
    Get the single optimal trail camera placement for mature buck hunting
    
    Returns one carefully calculated camera position based on:
    - Satellite vegetation analysis
    - Deer movement patterns  
    - Habitat edge locations
    - Optimal viewing angles
    """
    try:
        logger.info(f"🎥 Calculating optimal camera placement for ({lat:.4f}, {lon:.4f})")
        
        result = camera_system.calculate_optimal_camera_position(lat, lon)
        
        # Simplify response for frontend integration
        simplified_result = {
            "target_location": {
                "lat": lat,
                "lon": lon
            },
            "camera_placement": {
                "lat": result["optimal_camera"]["lat"],
                "lon": result["optimal_camera"]["lon"],
                "confidence_score": result["optimal_camera"]["confidence_score"],
                "distance_meters": result["optimal_camera"]["distance_from_target_meters"],
                "reasoning": result["placement_strategy"]["primary_factors"][0] if result["placement_strategy"]["primary_factors"] else "Optimal positioning based on terrain analysis"
            },
            "analysis_quality": {
                "data_source": result["satellite_data_quality"].get("data_source", "standard"),
                "confidence_level": "high" if result["optimal_camera"]["confidence_score"] >= 80 else "moderate"
            },
            "usage_instructions": {
                "detection_range": result["placement_strategy"]["expected_detection_range"],
                "optimal_times": result["placement_strategy"]["optimal_times"],
                "placement_type": result["placement_strategy"]["placement_type"]
            }
        }
        
        logger.info(f"✅ Camera placement calculated: {result['optimal_camera']['confidence_score']:.1f}% confidence")
        return simplified_result
        
    except Exception as e:
        logger.error(f"❌ Camera placement error: {e}")
        return {
            "error": "Camera placement calculation failed",
            "target_location": {"lat": lat, "lon": lon},
            "fallback_placement": {
                "lat": lat + 0.0005,  # ~50m northeast offset
                "lon": lon + 0.0007,
                "confidence_score": 60.0,
                "distance_meters": 75,
                "reasoning": "Fallback positioning due to analysis error"
            }
        }


def test_api_endpoint():
    """Test the API endpoint functionality"""
    import asyncio
    
    async def run_test():
        print("🧪 Testing Camera Placement API Endpoint")
        print("=" * 50)
        
        # Test Vermont location
        result = await get_optimal_camera_placement(44.26, -72.58)
        
        print(f"📍 Target: (44.26, -72.58)")
        if "error" not in result:
            camera = result["camera_placement"]
            print(f"🎥 Camera: ({camera['lat']:.6f}, {camera['lon']:.6f})")
            print(f"📏 Distance: {camera['distance_meters']:.0f}m")
            print(f"🎯 Confidence: {camera['confidence_score']:.1f}%")
            print(f"🧠 Reasoning: {camera['reasoning']}")
            print(f"✅ API endpoint working correctly!")
        else:
            print(f"❌ API error: {result['error']}")
            
        return result
    
    return asyncio.run(run_test())


if __name__ == "__main__":
    test_result = test_api_endpoint()
    print(f"\n📋 API Response Preview:")
    import json
    print(json.dumps(test_result, indent=2))
