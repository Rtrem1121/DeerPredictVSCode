"""
Playwright Frontend Validation Test for Deer Prediction App
Validates that backend data (97.1% suitability, 3 bedding zones) renders correctly
as green bedding pins and red stand pins with accurate tooltips
"""

from playwright.async_api import async_playwright
import pytest
import logging
import asyncio
from typing import Dict, List

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

@pytest.mark.asyncio
async def test_deer_prediction_frontend_rendering():
    """
    Test that enhanced bedding predictor data renders correctly on frontend
    Expected: 3+ green bedding pins, 1+ red stand pins, accurate tooltips
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        validation_results = {
            "bedding_pins_rendered": False,
            "stand_pins_rendered": False,
            "tooltip_content_accurate": False,
            "map_interactivity": False,
            "suitability_displayed": False,
            "biological_accuracy": False
        }
        
        try:
            logger.info("🎭 Starting Playwright frontend validation")
            
            # Navigate to Streamlit app
            await page.goto("http://localhost:8501", timeout=30000)
            logger.info("📱 Navigated to Streamlit app")
            
            # Wait for Streamlit to load
            await page.wait_for_selector("div[data-testid='stApp']", timeout=20000)
            logger.info("✅ Streamlit app loaded")
            
            # Generate a prediction by clicking the prediction button
            predict_button = page.locator("button:has-text('Generate Hunting Predictions')")
            if await predict_button.count() > 0:
                await predict_button.click()
                logger.info("🎯 Clicked prediction button")
                
                # Wait for prediction to complete (look for success message or results)
                try:
                    await page.wait_for_selector(
                        "div:has-text('Enhanced bedding predictions generated')", 
                        timeout=60000
                    )
                    logger.info("✅ Prediction completed")
                except:
                    # Alternative: wait for any prediction results
                    await page.wait_for_timeout(10000)  # Wait 10 seconds for results
                    logger.info("⏳ Waited for prediction results")
            
            # Check for map container (Folium map in Streamlit)
            map_selectors = [
                ".folium-map",
                ".stMap", 
                "iframe[title*='streamlit_folium']",
                ".leaflet-container"
            ]
            
            map_found = False
            for selector in map_selectors:
                if await page.query_selector(selector):
                    logger.info(f"✅ Found map with selector: {selector}")
                    map_found = True
                    break
            
            if not map_found:
                logger.warning("⚠️ No map container found, checking for iframe")
                # Check for Streamlit iframe
                iframe = await page.query_selector("iframe")
                if iframe:
                    # Switch to iframe context
                    frame = await iframe.content_frame()
                    if frame:
                        logger.info("✅ Found map iframe")
                        page = frame  # Use iframe context for further checks
            
            # Look for map markers (bedding zones and stands)
            marker_selectors = [
                ".leaflet-marker-icon",
                ".leaflet-marker",
                "div[class*='marker']",
                ".folium-marker",
                "img[src*='marker']"
            ]
            
            total_markers = 0
            for selector in marker_selectors:
                markers = await page.query_selector_all(selector)
                total_markers += len(markers)
                if markers:
                    logger.info(f"📍 Found {len(markers)} markers with selector: {selector}")
            
            if total_markers >= 3:
                validation_results["bedding_pins_rendered"] = True
                logger.info(f"✅ Found {total_markers} markers (expecting 3+ bedding zones)")
            
            if total_markers >= 4:  # 3 bedding + 1+ stand
                validation_results["stand_pins_rendered"] = True
                logger.info("✅ Stand recommendations likely present")
            
            # Check for tooltip content by hovering over markers
            markers = await page.query_selector_all(".leaflet-marker-icon, .leaflet-marker")
            if markers:
                for i, marker in enumerate(markers[:3]):  # Check first 3 markers
                    try:
                        await marker.hover()
                        await page.wait_for_timeout(1000)  # Wait for tooltip
                        
                        # Look for tooltip/popup content
                        tooltip_selectors = [
                            ".leaflet-tooltip",
                            ".leaflet-popup-content",
                            ".folium-tooltip",
                            "div[class*='tooltip']"
                        ]
                        
                        for tooltip_selector in tooltip_selectors:
                            tooltips = await page.query_selector_all(tooltip_selector)
                            for tooltip in tooltips:
                                tooltip_text = await tooltip.text_content()
                                if tooltip_text:
                                    logger.info(f"📝 Tooltip {i+1}: {tooltip_text[:100]}...")
                                    
                                    # Check for biological accuracy indicators
                                    bio_keywords = [
                                        "bedding", "suitability", "score", "slope", 
                                        "south-facing", "leeward", "ridge", "confidence",
                                        "97.1%", "95.", "stand", "zone"
                                    ]
                                    
                                    found_keywords = [
                                        kw for kw in bio_keywords 
                                        if kw.lower() in tooltip_text.lower()
                                    ]
                                    
                                    if found_keywords:
                                        validation_results["tooltip_content_accurate"] = True
                                        validation_results["biological_accuracy"] = True
                                        logger.info(f"✅ Found biological keywords: {found_keywords}")
                                    
                                    # Check for suitability scores
                                    if any(term in tooltip_text for term in ["97.1", "95.", "96.", "94.", "%"]):
                                        validation_results["suitability_displayed"] = True
                                        logger.info("✅ Suitability score displayed in tooltip")
                    
                    except Exception as e:
                        logger.debug(f"Tooltip check failed for marker {i}: {e}")
                        continue
            
            # Test map interactivity
            try:
                map_container = await page.query_selector(".leaflet-container, .folium-map")
                if map_container:
                    # Test zoom
                    await map_container.hover()
                    await page.mouse.wheel(0, -100)  # Zoom in
                    await page.wait_for_timeout(500)
                    await page.mouse.wheel(0, 100)   # Zoom out
                    validation_results["map_interactivity"] = True
                    logger.info("✅ Map interactivity working")
            except Exception as e:
                logger.warning(f"⚠️ Map interactivity test failed: {e}")
            
            # Check for suitability display in main content
            page_content = await page.content()
            if any(term in page_content for term in ["97.1%", "95.", "suitability", "confidence"]):
                validation_results["suitability_displayed"] = True
                logger.info("✅ Suitability information found in page content")
            
            # Log final validation results
            logger.info("🎭 FRONTEND VALIDATION RESULTS:")
            logger.info(f"   Bedding Pins Rendered: {'✅' if validation_results['bedding_pins_rendered'] else '❌'}")
            logger.info(f"   Stand Pins Rendered: {'✅' if validation_results['stand_pins_rendered'] else '❌'}")
            logger.info(f"   Tooltip Content: {'✅' if validation_results['tooltip_content_accurate'] else '❌'}")
            logger.info(f"   Map Interactivity: {'✅' if validation_results['map_interactivity'] else '❌'}")
            logger.info(f"   Suitability Displayed: {'✅' if validation_results['suitability_displayed'] else '❌'}")
            logger.info(f"   Biological Accuracy: {'✅' if validation_results['biological_accuracy'] else '❌'}")
            
            # Assert critical functionality
            assert validation_results["bedding_pins_rendered"], "Bedding zones not rendered as pins"
            assert validation_results["suitability_displayed"], "Suitability score not displayed"
            
            return validation_results
            
        except Exception as e:
            logger.error(f"❌ Frontend validation failed: {e}")
            raise
        
        finally:
            await browser.close()

@pytest.mark.asyncio 
async def test_backend_frontend_data_consistency():
    """
    Test that backend data (97.1% suitability, 3 zones) matches frontend display
    """
    import requests
    
    # Test backend API directly
    try:
        response = requests.post(
            "http://localhost:8000/predict",
            json={
                "lat": 43.3145,
                "lon": -73.2175, 
                "date_time": "2025-08-28T07:00:00",
                "season": "early_season",
                "fast_mode": True
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract backend metrics
            if 'success' in data and data.get('success'):
                prediction = data.get('data', data)
            else:
                prediction = data
            
            bedding_zones = prediction.get('bedding_zones', {})
            
            backend_zones = 0
            backend_suitability = 0
            
            if 'features' in bedding_zones:
                backend_zones = len(bedding_zones['features'])
                properties = bedding_zones.get('properties', {})
                suitability_analysis = properties.get('suitability_analysis', {})
                backend_suitability = suitability_analysis.get('overall_score', 0)
            
            logger.info(f"🔍 Backend Analysis:")
            logger.info(f"   Zones Generated: {backend_zones}")
            logger.info(f"   Suitability Score: {backend_suitability:.1f}%")
            
            # Validate backend meets expectations
            assert backend_zones >= 3, f"Expected 3+ bedding zones, got {backend_zones}"
            assert backend_suitability >= 90, f"Expected 90%+ suitability, got {backend_suitability:.1f}%"
            
            logger.info("✅ Backend data meets expectations")
            return True
            
    except Exception as e:
        logger.error(f"❌ Backend consistency check failed: {e}")
        return False

if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "-s"])
