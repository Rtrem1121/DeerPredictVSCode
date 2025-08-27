import logging
import sys
from datetime import datetime

def setup_logging():
    """Configure logging for the application"""
    # Create logs directory if it doesn't exist
    import os
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, f'deer_pred_{datetime.now().strftime("%Y%m%d")}.log')),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

class APIError(Exception):
    """Custom exception for API-related errors"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class DataValidationError(Exception):
    """Custom exception for data validation errors"""
    pass

class ExternalServiceError(Exception):
    """Custom exception for external service failures"""
    def __init__(self, service_name: str, message: str):
        self.service_name = service_name
        self.message = message
        super().__init__(f"{service_name}: {message}")
