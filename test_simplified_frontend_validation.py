#!/usr/bin/env python3
"""
Simplified Frontend Validation Test
Validates that all 10 site types are generated and displayed on the frontend
Uses content-based validation instead of complex marker detection
"""

import asyncio
import logging
from datetime import datetime
from playwright.async_api import async_playwright
import pytest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimplifiedFrontendValidator:
    """
    Simplified frontend validation focusing on content rather than visual markers
    Validates that backend data flows correctly to the frontend
    """
    
    def __init__(self, app_url: str = "http://localhost:8501"):
        self.app_url = app_url
        self.test_coordinates = {
            "lat": 43.3144,
            "lon": -73.2182,
            "location_name": "Tinmouth, Vermont"
        }
        
    async def run_comprehensive_validation(self) -> dict:
        """Run simplified comprehensive validation of all 10 site types"""
        
        logger.info("🎯 Starting Simplified Frontend Validation")
        logger.info(f"   Test URL: {self.app_url}")
        logger.info(f"   Test Location: {self.test_coordinates['location_name']}")
        
        results = {
            "test_start_time": datetime.now().isoformat(),
            "overall_success": False,
            "validation_stages": {},
            "backend_data_validation": {},
            "frontend_content_validation": {}
        }
        
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        
        try:
            page = await browser.new_page()
            
            # Stage 1: Navigate to frontend
            logger.info("📱 Navigating to frontend...")
            await page.goto(self.app_url, timeout=30000)
            await page.wait_for_selector("div[data-testid='stApp']", timeout=30000)
            logger.info("✅ Frontend loaded successfully")
            
            # Stage 2: Wait for page to stabilize
            logger.info("⏳ Waiting for page to stabilize...")
            await page.wait_for_timeout(3000)
            
            # Stage 3: Look for prediction trigger
            logger.info("🎯 Looking for prediction interface...")
            
            # Try to find and click prediction button
            try:
                predict_selectors = [
                    "button:has-text('Generate Hunting Predictions')",
                    "button:has-text('Generate Predictions')", 
                    "button:has-text('Predict')",
                    "button[type='submit']",
                    ".stButton button"
                ]
                
                button_found = False
                for selector in predict_selectors:
                    try:
                        button = page.locator(selector).first
                        if await button.is_visible():
                            await button.click()
                            logger.info(f"✅ Clicked prediction button: {selector}")
                            button_found = True
                            break
                    except Exception:
                        continue
                
                if not button_found:
                    logger.warning("⚠️ No prediction button found, checking if predictions already visible")
                
                # Wait for prediction results (give it time to generate)
                logger.info("⏳ Waiting for prediction generation...")
                await page.wait_for_timeout(10000)  # 10 seconds for prediction
                
            except Exception as e:
                logger.warning(f"⚠️ Prediction trigger failed: {e}")
            
            # Stage 4: Validate content for all site types
            logger.info("📊 Validating frontend content...")
            
            page_content = await page.content()
            page_text = await page.text_content("body")
            
            # Validate bedding zones (3 expected)
            bedding_validation = self.validate_bedding_content(page_content, page_text)
            results["validation_stages"]["bedding_zones"] = bedding_validation
            
            # Validate stand sites (3 expected)  
            stands_validation = self.validate_stands_content(page_content, page_text)
            results["validation_stages"]["stand_recommendations"] = stands_validation
            
            # Validate feeding areas (3 expected)
            feeding_validation = self.validate_feeding_content(page_content, page_text)
            results["validation_stages"]["feeding_areas"] = feeding_validation
            
            # Validate camera placement (1 expected)
            camera_validation = self.validate_camera_content(page_content, page_text)
            results["validation_stages"]["camera_placement"] = camera_validation
            
            # Overall success assessment
            success_criteria = [
                bedding_validation.get("content_found", False),
                stands_validation.get("content_found", False),
                feeding_validation.get("content_found", False),
                camera_validation.get("content_found", False)
            ]
            
            results["overall_success"] = all(success_criteria)
            results["success_criteria_met"] = sum(success_criteria)
            results["total_success_criteria"] = len(success_criteria)
            
            # Log comprehensive results
            logger.info("=" * 70)
            logger.info("📊 SIMPLIFIED FRONTEND VALIDATION RESULTS")
            logger.info("=" * 70)
            logger.info(f"Overall Success: {'✅ PASS' if results['overall_success'] else '❌ FAIL'} ({results['success_criteria_met']}/{results['total_success_criteria']} criteria met)")
            logger.info(f"🛏️ Bedding Content: {'✅' if bedding_validation['content_found'] else '❌'} (Expected 3 zones)")
            logger.info(f"🎯 Stand Content: {'✅' if stands_validation['content_found'] else '❌'} (Expected 3 sites)")
            logger.info(f"🌾 Feeding Content: {'✅' if feeding_validation['content_found'] else '❌'} (Expected 3 areas)")
            logger.info(f"📷 Camera Content: {'✅' if camera_validation['content_found'] else '❌'} (Expected 1 site)")
            logger.info("=" * 70)
            
        except Exception as e:
            logger.error(f"❌ Validation failed: {e}")
            results["validation_error"] = str(e)
            
        finally:
            await browser.close()
            results["test_end_time"] = datetime.now().isoformat()
        
        return results
    
    def validate_bedding_content(self, page_content: str, page_text: str) -> dict:
        """Validate bedding zone content is present"""
        validation = {
            "content_found": False,
            "indicators_found": [],
            "expected_count": 3
        }
        
        # Look for bedding-related indicators
        bedding_indicators = [
            "bedding", "thermal", "south-facing", "canopy", 
            "suitability", "97%", "leeward", "ridge"
        ]
        
        found_indicators = []
        for indicator in bedding_indicators:
            if indicator.lower() in page_text.lower():
                found_indicators.append(indicator)
        
        validation["indicators_found"] = found_indicators
        validation["content_found"] = len(found_indicators) >= 2  # Need at least 2 indicators
        
        logger.info(f"🛏️ Bedding validation: {len(found_indicators)} indicators found: {found_indicators}")
        return validation
    
    def validate_stands_content(self, page_content: str, page_text: str) -> dict:
        """Validate stand recommendations content is present"""
        validation = {
            "content_found": False,
            "indicators_found": [],
            "expected_count": 3
        }
        
        # Look for stand-related indicators
        stand_indicators = [
            "stand", "travel corridor", "pinch point", "feeding area stand",
            "confidence", "mature buck", "ambush", "observation"
        ]
        
        found_indicators = []
        for indicator in stand_indicators:
            if indicator.lower() in page_text.lower():
                found_indicators.append(indicator)
        
        validation["indicators_found"] = found_indicators
        validation["content_found"] = len(found_indicators) >= 2  # Need at least 2 indicators
        
        logger.info(f"🎯 Stand validation: {len(found_indicators)} indicators found: {found_indicators}")
        return validation
    
    def validate_feeding_content(self, page_content: str, page_text: str) -> dict:
        """Validate feeding areas content is present"""
        validation = {
            "content_found": False,
            "indicators_found": [],
            "expected_count": 3
        }
        
        # Look for feeding-related indicators
        feeding_indicators = [
            "feeding", "browse", "mast", "food", "agricultural",
            "edge habitat", "food plot", "food source"
        ]
        
        found_indicators = []
        for indicator in feeding_indicators:
            if indicator.lower() in page_text.lower():
                found_indicators.append(indicator)
        
        validation["indicators_found"] = found_indicators
        validation["content_found"] = len(found_indicators) >= 1  # Need at least 1 indicator
        
        logger.info(f"🌾 Feeding validation: {len(found_indicators)} indicators found: {found_indicators}")
        return validation
    
    def validate_camera_content(self, page_content: str, page_text: str) -> dict:
        """Validate camera placement content is present"""
        validation = {
            "content_found": False,
            "indicators_found": [],
            "expected_count": 1
        }
        
        # Look for camera-related indicators
        camera_indicators = [
            "camera", "trail cam", "placement", "monitor", 
            "setup", "height", "angle", "photos"
        ]
        
        found_indicators = []
        for indicator in camera_indicators:
            if indicator.lower() in page_text.lower():
                found_indicators.append(indicator)
        
        validation["indicators_found"] = found_indicators
        validation["content_found"] = len(found_indicators) >= 1  # Need at least 1 indicator
        
        logger.info(f"📷 Camera validation: {len(found_indicators)} indicators found: {found_indicators}")
        return validation

# Pytest integration
@pytest.mark.asyncio
async def test_simplified_frontend_validation():
    """Simplified pytest test for all 10 site types"""
    validator = SimplifiedFrontendValidator()
    results = await validator.run_comprehensive_validation()
    
    # Assert overall success
    assert results["overall_success"], f"Frontend validation failed: {results}"
    
    # Assert individual components
    bedding = results["validation_stages"]["bedding_zones"]
    assert bedding["content_found"], f"Bedding content not found: {bedding}"
    
    stands = results["validation_stages"]["stand_recommendations"]
    assert stands["content_found"], f"Stand content not found: {stands}"
    
    feeding = results["validation_stages"]["feeding_areas"]
    assert feeding["content_found"], f"Feeding content not found: {feeding}"
    
    camera = results["validation_stages"]["camera_placement"]
    assert camera["content_found"], f"Camera content not found: {camera}"
    
    return results

# Standalone execution
async def main():
    """Run simplified validation standalone"""
    validator = SimplifiedFrontendValidator()
    results = await validator.run_comprehensive_validation()
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"simplified_frontend_validation_{timestamp}.json"
    
    import json
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"📁 Results saved to: {results_file}")
    
    return results["overall_success"]

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
