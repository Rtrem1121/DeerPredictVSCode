#!/usr/bin/env python3
"""
Google Earth Engine Diagnostic Tool

Comprehensive diagnostic to identify and fix GEE authentication issues
for the Vermont Food Prediction System.

Author: Vermont Deer Prediction System
Date: October 2, 2025
"""

import os
import sys
import json
import logging
from typing import Dict, Tuple
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

class GEEDiagnostic:
    """Comprehensive GEE authentication diagnostic"""
    
    def __init__(self):
        self.results = {
            'environment_vars': {},
            'file_checks': {},
            'credential_validation': {},
            'gee_initialization': {},
            'vermont_test': {},
            'recommendations': []
        }
        
    def check_environment_variables(self) -> Dict:
        """Check GEE-related environment variables"""
        logger.info("\n" + "="*60)
        logger.info("1️⃣  CHECKING ENVIRONMENT VARIABLES")
        logger.info("="*60)
        
        env_vars = {
            'GOOGLE_APPLICATION_CREDENTIALS': os.getenv('GOOGLE_APPLICATION_CREDENTIALS'),
            'GEE_PROJECT_ID': os.getenv('GEE_PROJECT_ID'),
            'PYTHONPATH': os.getenv('PYTHONPATH')
        }
        
        for var_name, var_value in env_vars.items():
            status = "✅" if var_value else "❌"
            logger.info(f"  {status} {var_name}: {var_value or 'NOT SET'}")
            
        self.results['environment_vars'] = env_vars
        
        if not env_vars['GOOGLE_APPLICATION_CREDENTIALS']:
            self.results['recommendations'].append(
                "Set GOOGLE_APPLICATION_CREDENTIALS environment variable"
            )
        
        return env_vars
    
    def check_credential_files(self) -> Dict:
        """Check for credential files in expected locations"""
        logger.info("\n" + "="*60)
        logger.info("2️⃣  CHECKING CREDENTIAL FILES")
        logger.info("="*60)
        
        possible_paths = [
            'credentials/gee-service-account.json',
            '/app/credentials/gee-service-account.json',
            '/app/config/deer-pred-service-account.json'
        ]
        
        file_checks = {}
        found_valid = False
        
        for path in possible_paths:
            exists = os.path.exists(path)
            file_checks[path] = {
                'exists': exists,
                'readable': False,
                'valid_json': False,
                'is_service_account': False,
                'size': 0
            }
            
            status = "✅" if exists else "❌"
            logger.info(f"  {status} {path}: {'Found' if exists else 'Not found'}")
            
            if exists:
                try:
                    # Check if readable
                    file_checks[path]['readable'] = os.access(path, os.R_OK)
                    file_checks[path]['size'] = os.path.getsize(path)
                    
                    # Check if valid JSON
                    with open(path, 'r') as f:
                        creds = json.load(f)
                        file_checks[path]['valid_json'] = True
                        
                        # Check if service account
                        if creds.get('type') == 'service_account':
                            file_checks[path]['is_service_account'] = True
                            found_valid = True
                            logger.info(f"    ✅ Valid service account: {creds.get('client_email', 'unknown')}")
                            logger.info(f"    ✅ Project ID: {creds.get('project_id', 'unknown')}")
                        else:
                            logger.warning(f"    ⚠️  Not a service account (type: {creds.get('type')})")
                            
                except json.JSONDecodeError as e:
                    logger.error(f"    ❌ Invalid JSON: {e}")
                except Exception as e:
                    logger.error(f"    ❌ Error reading file: {e}")
        
        self.results['file_checks'] = file_checks
        
        if not found_valid:
            self.results['recommendations'].append(
                "Create valid service account credentials in credentials/gee-service-account.json"
            )
        
        return file_checks
    
    def test_gee_import(self) -> Dict:
        """Test if Earth Engine library can be imported"""
        logger.info("\n" + "="*60)
        logger.info("3️⃣  TESTING EARTH ENGINE LIBRARY")
        logger.info("="*60)
        
        try:
            import ee
            logger.info("  ✅ Earth Engine library imported successfully")
            self.results['gee_initialization']['import'] = True
            return {'success': True, 'error': None}
        except ImportError as e:
            logger.error(f"  ❌ Failed to import Earth Engine: {e}")
            self.results['gee_initialization']['import'] = False
            self.results['recommendations'].append("Install earthengine-api: pip install earthengine-api")
            return {'success': False, 'error': str(e)}
    
    def test_gee_authentication(self) -> Dict:
        """Test GEE authentication with available credentials"""
        logger.info("\n" + "="*60)
        logger.info("4️⃣  TESTING GEE AUTHENTICATION")
        logger.info("="*60)
        
        try:
            import ee
            
            # Try to find valid credentials
            creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            if not creds_path or not os.path.exists(creds_path):
                # Try default locations
                for path in ['credentials/gee-service-account.json', 
                           '/app/credentials/gee-service-account.json']:
                    if os.path.exists(path):
                        creds_path = path
                        break
            
            if creds_path and os.path.exists(creds_path):
                logger.info(f"  🔑 Using credentials: {creds_path}")
                
                # Try service account authentication
                try:
                    credentials = ee.ServiceAccountCredentials(None, creds_path)
                    ee.Initialize(credentials)
                    logger.info("  ✅ Service account authentication successful")
                    
                    # Test basic functionality
                    test_value = ee.Number(42).getInfo()
                    if test_value == 42:
                        logger.info("  ✅ GEE API connection verified (test: 42 == 42)")
                        self.results['gee_initialization']['authenticated'] = True
                        self.results['gee_initialization']['method'] = 'service_account'
                        return {'success': True, 'method': 'service_account'}
                    else:
                        raise Exception(f"Test failed: expected 42, got {test_value}")
                        
                except Exception as e:
                    logger.error(f"  ❌ Service account auth failed: {e}")
                    self.results['gee_initialization']['authenticated'] = False
                    self.results['gee_initialization']['error'] = str(e)
                    return {'success': False, 'error': str(e)}
            else:
                logger.warning("  ⚠️  No credentials found, attempting default authentication")
                try:
                    ee.Initialize()
                    test_value = ee.Number(42).getInfo()
                    if test_value == 42:
                        logger.info("  ✅ Default authentication successful")
                        self.results['gee_initialization']['authenticated'] = True
                        self.results['gee_initialization']['method'] = 'default'
                        return {'success': True, 'method': 'default'}
                except Exception as e:
                    logger.error(f"  ❌ Default authentication failed: {e}")
                    self.results['gee_initialization']['authenticated'] = False
                    self.results['recommendations'].append(
                        "Run 'earthengine authenticate' or provide service account credentials"
                    )
                    return {'success': False, 'error': str(e)}
                    
        except Exception as e:
            logger.error(f"  ❌ Authentication test failed: {e}")
            self.results['gee_initialization']['authenticated'] = False
            return {'success': False, 'error': str(e)}
    
    def test_vermont_location(self) -> Dict:
        """Test actual Vermont food classification"""
        logger.info("\n" + "="*60)
        logger.info("5️⃣  TESTING VERMONT FOOD CLASSIFICATION")
        logger.info("="*60)
        
        try:
            import ee
            
            # Vermont hunting location (example)
            test_lat = 43.3115
            test_lon = -73.2149
            
            logger.info(f"  📍 Test location: {test_lat}, {test_lon} (Vermont)")
            
            # Create test point
            point = ee.Geometry.Point([test_lon, test_lat])
            logger.info("  ✅ Created Vermont geometry point")
            
            # Test USDA CDL access
            try:
                cdl = ee.ImageCollection("USDA/NASS/CDL") \
                    .filter(ee.Filter.date('2024-01-01', '2024-12-31')) \
                    .first()
                logger.info("  ✅ USDA Cropland Data Layer accessible")
                
                # Sample CDL at point
                buffer = point.buffer(100)
                sample = cdl.select('cropland').reduceRegion(
                    reducer=ee.Reducer.mode(),
                    geometry=buffer,
                    scale=30
                ).getInfo()
                
                crop_code = sample.get('cropland', 'unknown')
                logger.info(f"  ✅ CDL sampled successfully: crop code {crop_code}")
                
            except Exception as e:
                logger.error(f"  ❌ CDL access failed: {e}")
                self.results['vermont_test']['cdl_access'] = False
                return {'success': False, 'error': str(e)}
            
            # Test NDVI access
            try:
                ndvi = ee.ImageCollection('COPERNICUS/S2_SR') \
                    .filterBounds(point) \
                    .filterDate('2024-06-01', '2024-09-01') \
                    .first() \
                    .normalizedDifference(['B8', 'B4'])
                
                ndvi_value = ndvi.reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=point.buffer(100),
                    scale=10
                ).getInfo()
                
                logger.info(f"  ✅ NDVI accessed successfully: {ndvi_value}")
                
            except Exception as e:
                logger.warning(f"  ⚠️  NDVI access failed (non-critical): {e}")
            
            # Test Vermont Food Classifier integration
            try:
                sys.path.insert(0, os.path.abspath('.'))
                from backend.vermont_food_classifier import get_vermont_food_classifier
                
                vt_classifier = get_vermont_food_classifier()
                logger.info("  ✅ Vermont Food Classifier imported")
                
                # Test spatial food grid
                result = vt_classifier.create_spatial_food_grid(
                    center_lat=test_lat,
                    center_lon=test_lon,
                    season='early_season',
                    grid_size=10
                )
                
                metadata = result.get('grid_metadata', {})
                is_fallback = metadata.get('fallback', False)
                mean_quality = metadata.get('mean_grid_quality', 0)
                
                if is_fallback:
                    logger.warning(f"  ⚠️  Food grid using FALLBACK mode (quality: {mean_quality})")
                    logger.warning("  ⚠️  GEE data not accessible - returning uniform scores")
                    self.results['vermont_test']['using_fallback'] = True
                    self.results['recommendations'].append(
                        "Fix GEE authentication to enable real Vermont food classification"
                    )
                else:
                    logger.info(f"  ✅ Food grid using REAL GEE DATA (mean quality: {mean_quality:.2f})")
                    patches = result.get('food_patch_locations', [])
                    logger.info(f"  ✅ Found {len(patches)} high-quality food patches")
                    if patches:
                        best = patches[0]
                        logger.info(f"  🌽 Best food source: {best['lat']:.4f}, {best['lon']:.4f} (quality: {best['quality']:.2f})")
                    self.results['vermont_test']['using_fallback'] = False
                
                self.results['vermont_test']['success'] = True
                return {'success': True, 'fallback': is_fallback}
                
            except Exception as e:
                logger.error(f"  ❌ Vermont classifier test failed: {e}")
                self.results['vermont_test']['success'] = False
                return {'success': False, 'error': str(e)}
                
        except Exception as e:
            logger.error(f"  ❌ Vermont location test failed: {e}")
            self.results['vermont_test']['success'] = False
            return {'success': False, 'error': str(e)}
    
    def print_summary(self):
        """Print diagnostic summary and recommendations"""
        logger.info("\n" + "="*60)
        logger.info("📊 DIAGNOSTIC SUMMARY")
        logger.info("="*60)
        
        # Overall status
        gee_working = (
            self.results.get('gee_initialization', {}).get('authenticated', False) and
            not self.results.get('vermont_test', {}).get('using_fallback', True)
        )
        
        if gee_working:
            logger.info("\n✅ GOOGLE EARTH ENGINE IS WORKING CORRECTLY")
            logger.info("   Vermont food classification is using real satellite data")
        else:
            logger.warning("\n⚠️  GOOGLE EARTH ENGINE IS NOT FULLY FUNCTIONAL")
            logger.warning("   Vermont food classification is using FALLBACK mode")
            logger.warning("   All food quality scores will be uniform (0.55)")
        
        # Print recommendations
        if self.results['recommendations']:
            logger.info("\n" + "="*60)
            logger.info("🔧 RECOMMENDATIONS TO FIX ISSUES")
            logger.info("="*60)
            for i, rec in enumerate(self.results['recommendations'], 1):
                logger.info(f"  {i}. {rec}")
        
        # Print next steps
        logger.info("\n" + "="*60)
        logger.info("📋 NEXT STEPS")
        logger.info("="*60)
        
        if not gee_working:
            logger.info("\n1️⃣  Create GEE Service Account:")
            logger.info("   • Go to: https://console.cloud.google.com/")
            logger.info("   • Create/select project: deer-predict-app")
            logger.info("   • Enable: Google Earth Engine API")
            logger.info("   • Create service account with Earth Engine access")
            logger.info("   • Download JSON key file")
            
            logger.info("\n2️⃣  Place Credentials:")
            logger.info("   • Save JSON as: credentials/gee-service-account.json")
            
            logger.info("\n3️⃣  Set Environment Variable:")
            logger.info("   • export GOOGLE_APPLICATION_CREDENTIALS=credentials/gee-service-account.json")
            
            logger.info("\n4️⃣  Test Again:")
            logger.info("   • python gee_diagnostic.py")
            
            logger.info("\n5️⃣  Restart Docker:")
            logger.info("   • docker-compose down")
            logger.info("   • docker-compose up -d")
            
        else:
            logger.info("\n✅ No action needed - GEE is working correctly!")
            logger.info("   Your Vermont food predictions are using real satellite data")
        
        logger.info("\n" + "="*60)
    
    def save_report(self, filename: str = "gee_diagnostic_report.json"):
        """Save diagnostic results to JSON file"""
        try:
            with open(filename, 'w') as f:
                json.dump(self.results, f, indent=2)
            logger.info(f"\n💾 Detailed report saved to: {filename}")
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
    
    def run_full_diagnostic(self):
        """Run complete diagnostic suite"""
        logger.info("\n" + "="*60)
        logger.info("🛰️  GOOGLE EARTH ENGINE DIAGNOSTIC TOOL")
        logger.info("    Vermont Food Prediction System")
        logger.info("="*60)
        
        # Run all checks
        self.check_environment_variables()
        self.check_credential_files()
        self.test_gee_import()
        self.test_gee_authentication()
        self.test_vermont_location()
        
        # Print summary
        self.print_summary()
        
        # Save report
        self.save_report()
        
        return self.results

def main():
    """Run diagnostic"""
    diagnostic = GEEDiagnostic()
    results = diagnostic.run_full_diagnostic()
    
    # Return exit code based on results
    gee_working = (
        results.get('gee_initialization', {}).get('authenticated', False) and
        not results.get('vermont_test', {}).get('using_fallback', True)
    )
    
    sys.exit(0 if gee_working else 1)

if __name__ == "__main__":
    main()
