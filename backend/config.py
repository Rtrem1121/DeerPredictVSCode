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
    grid_span_degrees: float = 0.04
    
    # API Settings
    api_timeout: int = 30
    elevation_api_delay: float = 2.0
    
    # Prediction Settings
    high_score_percentile: int = 85
    travel_corridor_percentile: int = 90
    
    # Caching (future enhancement)
    cache_enabled: bool = False
    cache_ttl_hours: int = 24

def get_config() -> Config:
    """Load configuration from environment variables"""
    api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    if not api_key:
        raise ValueError("OPENWEATHERMAP_API_KEY environment variable is required")
    
    return Config(
        openweathermap_api_key=api_key,
        grid_size=int(os.getenv("GRID_SIZE", "10")),
        grid_span_degrees=float(os.getenv("GRID_SPAN_DEGREES", "0.04")),
        api_timeout=int(os.getenv("API_TIMEOUT", "30")),
        elevation_api_delay=float(os.getenv("ELEVATION_API_DELAY", "2.0")),
        high_score_percentile=int(os.getenv("HIGH_SCORE_PERCENTILE", "85")),
        travel_corridor_percentile=int(os.getenv("TRAVEL_CORRIDOR_PERCENTILE", "90")),
        cache_enabled=os.getenv("CACHE_ENABLED", "false").lower() == "true",
        cache_ttl_hours=int(os.getenv("CACHE_TTL_HOURS", "24"))
    )
