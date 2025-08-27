import os
from typing import Optional
from dataclasses import dataclass

@dataclass
class Config:
    """Application configuration settings"""
    # API Keys
    openweathermap_api_key: str
    
    # Grid Analysis Settings
    grid_size: int = 10

def get_config() -> Config:
    """Load configuration from environment variables"""
    api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    if not api_key:
        raise ValueError("OPENWEATHERMAP_API_KEY environment variable is required")
    
    return Config(
        openweathermap_api_key=api_key,
        grid_size=int(os.getenv("GRID_SIZE", "10"))
    )
