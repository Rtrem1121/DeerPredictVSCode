"""
Google Earth Engine Setup for Docker
Handles service account authentication automatically
"""
import ee
import os
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class GEESetup:
    """Handle GEE authentication and initialization for Docker"""
    
    def __init__(self):
        self.initialized = False
        self.available = False
        self.project_id = os.getenv('GEE_PROJECT_ID', 'deer-predict-app')
        self.credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        
        # For Docker container, try the expected path first
        if not self.credentials_path:
            docker_creds = '/app/config/deer-pred-service-account.json'
            if os.path.exists(docker_creds):
                self.credentials_path = docker_creds
        
        # For local testing, try the local credentials path if env var not set
        if not self.credentials_path:
            local_creds = 'credentials/gee-service-account.json'
            if os.path.exists(local_creds):
                self.credentials_path = os.path.abspath(local_creds)
        
    def authenticate_service_account(self) -> bool:
        """Authenticate using service account credentials"""
        try:
            if not self.credentials_path:
                logger.warning("No GOOGLE_APPLICATION_CREDENTIALS environment variable set")
                return False
                
            if not os.path.exists(self.credentials_path):
                logger.warning(f"Credentials file not found: {self.credentials_path}")
                return False
            
            # Test if credentials are valid JSON
            with open(self.credentials_path, 'r') as f:
                credentials = json.load(f)
                if 'type' not in credentials or credentials['type'] != 'service_account':
                    logger.error("Invalid service account credentials format")
                    return False
            
            # Use the simplified method that works
            service_credentials = ee.ServiceAccountCredentials(None, self.credentials_path)
            ee.Initialize(service_credentials)
            
            logger.info("✅ GEE service account authentication successful")
            return True
            
        except Exception as e:
            logger.warning(f"GEE authentication failed: {e}")
            return False
    
    def initialize(self) -> bool:
        """Initialize Google Earth Engine"""
        try:
            if not self.initialized:
                # Try service account authentication first
                if self.credentials_path:
                    if not self.authenticate_service_account():
                        return False
                    
                    # Test basic functionality after service account auth
                    try:
                        test_result = ee.Number(1).getInfo()
                        if test_result == 1:
                            self.initialized = True
                            self.available = True
                            logger.info(f"✅ GEE initialized successfully with service account")
                            return True
                        else:
                            logger.error("GEE initialization test failed")
                            return False
                    except Exception as test_error:
                        logger.error(f"GEE test failed: {test_error}")
                        return False
                else:
                    # Fallback to default initialization if no service account
                    ee.Initialize(project=self.project_id)
                    
                    # Test basic functionality
                    test_result = ee.Number(1).getInfo()
                    if test_result == 1:
                        self.initialized = True
                        self.available = True
                        logger.info(f"✅ GEE initialized successfully with project: {self.project_id}")
                        return True
                    else:
                        logger.error("GEE initialization test failed")
                        return False
                    
        except Exception as e:
            logger.warning(f"GEE initialization failed: {e}")
            logger.info("🔄 App will use standard terrain analysis")
            return False
    
    def is_available(self) -> bool:
        """Check if GEE is available and initialized"""
        if not self.initialized:
            return self.initialize()
        return self.available
    
    def get_status(self) -> dict:
        """Get detailed status information"""
        return {
            "available": self.available,
            "initialized": self.initialized,
            "project_id": self.project_id,
            "credentials_configured": bool(self.credentials_path),
            "credentials_file_exists": bool(self.credentials_path and os.path.exists(self.credentials_path))
        }

# Global instance
gee_setup = GEESetup()

def test_gee_setup():
    """Test GEE setup in Docker environment"""
    print("🛰️ Testing Google Earth Engine Setup for Docker")
    print("=" * 50)
    
    status = gee_setup.get_status()
    print(f"Project ID: {status['project_id']}")
    print(f"Credentials configured: {status['credentials_configured']}")
    print(f"Credentials file exists: {status['credentials_file_exists']}")
    
    if gee_setup.is_available():
        print("✅ Google Earth Engine is ready!")
        
        # Test basic functionality
        try:
            point = ee.Geometry.Point(-72.58, 44.26)
            print("✅ Vermont coordinates accessible")
            
            # Test image access
            collection = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
                .filterBounds(point) \
                .filterDate('2024-06-01', '2024-09-01')
            
            count = collection.size().getInfo()
            print(f"✅ Found {count} Landsat images for Vermont area")
            
            print("🎉 Google Earth Engine fully operational!")
            
        except Exception as e:
            print(f"⚠️ GEE basic test failed: {e}")
    else:
        print("❌ Google Earth Engine not available")
        print("This is expected if running locally without service account credentials")
        print("In Docker with proper credentials, this should work")

if __name__ == "__main__":
    test_gee_setup()
