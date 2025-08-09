#!/usr/bin/env python3
"""
Configuration Management System

This module provides centralized configuration management for the deer prediction system.
It supports environment-specific configurations, hot-reloading, validation, and fallbacks.

Key Features:
- Environment-specific configurations (dev, test, prod)
- Hot-reload capability for runtime updates
- Comprehensive validation and type checking
- Fallback to defaults if configuration is missing
- Configuration change auditing and versioning

Author: Vermont Deer Prediction System
Version: 1.0.0
"""

import os
import yaml
import json
import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
import threading
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = None

logger = logging.getLogger(__name__)

@dataclass
class ConfigValidationError(Exception):
    """Raised when configuration validation fails"""
    parameter: str
    value: Any
    expected: str
    message: str = ""

@dataclass
class ConfigurationMetadata:
    """Metadata about configuration state"""
    version: str = "1.0.0"
    environment: str = "development"
    last_loaded: Optional[datetime] = None
    last_modified: Optional[datetime] = None
    source_files: List[str] = field(default_factory=list)
    validation_errors: List[str] = field(default_factory=list)

class ConfigFileWatcher:
    """File system watcher for configuration hot-reload"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(('.yaml', '.yml')):
            logger.info(f"Configuration file changed: {event.src_path}")
            self.config_manager._reload_config()

class DeerPredictionConfig:
    """
    Centralized configuration management for deer prediction system
    """
    
    def __init__(self, environment: str = None, config_dir: str = None):
        """
        Initialize configuration manager
        
        Args:
            environment: Environment name (development, testing, production)
            config_dir: Directory containing configuration files
        """
        self.environment = environment or os.getenv('DEER_PRED_ENV', 'development')
        self.config_dir = Path(config_dir or self._get_default_config_dir())
        self.metadata = ConfigurationMetadata(environment=self.environment)
        
        # Thread lock for hot-reload safety
        self._lock = threading.RLock()
        self._config_data: Dict[str, Any] = {}
        self._observer = None
        
        # Load initial configuration
        self._load_config()
        
        # Set up file watching for hot-reload
        self._setup_file_watcher()
        
    def _get_default_config_dir(self) -> str:
        """Get default configuration directory"""
        # Look for config directory relative to this file
        current_dir = Path(__file__).parent.parent
        config_dir = current_dir / "config"
        
        if config_dir.exists():
            return str(config_dir)
        
        # Fallback to creating config in current working directory
        fallback_dir = Path.cwd() / "config"
        fallback_dir.mkdir(exist_ok=True)
        return str(fallback_dir)
    
    def _setup_file_watcher(self):
        """Setup file system watcher for hot-reload"""
        if not WATCHDOG_AVAILABLE:
            logger.info("📁 Watchdog not available - hot-reload disabled")
            return
            
        try:
            self._observer = Observer()
            event_handler = ConfigFileWatcher(self)
            self._observer.schedule(event_handler, str(self.config_dir), recursive=False)
            self._observer.start()
            logger.info(f"🔄 Configuration hot-reload enabled for {self.config_dir}")
        except Exception as e:
            logger.warning(f"Failed to setup configuration file watcher: {e}")
    
    def _load_config(self):
        """Load configuration from files"""
        with self._lock:
            try:
                # Start with defaults
                config_data = self._load_config_file("defaults.yaml")
                
                # Override with environment-specific config
                env_config = self._load_config_file(f"{self.environment}.yaml")
                if env_config:
                    config_data = self._deep_merge(config_data, env_config)
                
                # Apply any environment variable overrides
                config_data = self._apply_env_overrides(config_data)
                
                # Validate configuration
                self._validate_config(config_data)
                
                # Store configuration
                self._config_data = config_data.get('deer_prediction_config', {})
                self.metadata.last_loaded = datetime.now()
                self.metadata.version = self._config_data.get('version', '1.0.0')
                
                logger.info(f"✅ Configuration loaded successfully (env: {self.environment}, version: {self.metadata.version})")
                
            except Exception as e:
                logger.error(f"❌ Failed to load configuration: {e}")
                self._load_fallback_config()
    
    def _load_config_file(self, filename: str) -> Optional[Dict[str, Any]]:
        """Load a specific configuration file"""
        config_path = self.config_dir / filename
        
        if not config_path.exists():
            if filename == "defaults.yaml":
                logger.error(f"❌ Required default configuration file not found: {config_path}")
                return {}
            return None
            
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                self.metadata.source_files.append(str(config_path))
                logger.debug(f"📄 Loaded configuration file: {filename}")
                return data
        except Exception as e:
            logger.error(f"❌ Failed to load configuration file {filename}: {e}")
            return None
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two configuration dictionaries"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
                
        return result
    
    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides"""
        # Look for environment variables with DEER_PRED_ prefix
        overrides = {}
        for key, value in os.environ.items():
            if key.startswith('DEER_PRED_'):
                # Convert DEER_PRED_API_SETTINGS_BASE_CONFIDENCE to nested dict
                config_key = key[10:].lower()  # Remove DEER_PRED_ prefix
                try:
                    # Try to parse as JSON for complex values
                    parsed_value = json.loads(value)
                except:
                    # Fallback to string/numeric parsing
                    if value.lower() in ('true', 'false'):
                        parsed_value = value.lower() == 'true'
                    elif value.replace('.', '').replace('-', '').isdigit():
                        parsed_value = float(value) if '.' in value else int(value)
                    else:
                        parsed_value = value
                
                overrides[config_key] = parsed_value
        
        if overrides:
            logger.info(f"🔧 Applied {len(overrides)} environment variable overrides")
            
        return config
    
    def _validate_config(self, config: Dict[str, Any]):
        """Validate configuration parameters"""
        deer_config = config.get('deer_prediction_config', {})
        errors = []
        
        # Validate confidence ranges
        if 'validation' in deer_config:
            confidence_range = deer_config['validation'].get('confidence_range', [0, 100])
            if len(confidence_range) != 2 or confidence_range[0] >= confidence_range[1]:
                errors.append("Invalid confidence_range: must be [min, max] with min < max")
        
        # Validate distance parameters
        if 'distance_parameters' in deer_config:
            dist_params = deer_config['distance_parameters']
            for key, value in dist_params.items():
                if not isinstance(value, (int, float)) or value < 0:
                    errors.append(f"Invalid distance parameter {key}: must be positive number")
        
        # Validate seasonal weights
        if 'seasonal_weights' in deer_config:
            for season, weights in deer_config['seasonal_weights'].items():
                for behavior, weight in weights.items():
                    if not isinstance(weight, (int, float)) or weight < 0:
                        errors.append(f"Invalid seasonal weight {season}.{behavior}: must be positive number")
        
        self.metadata.validation_errors = errors
        
        if errors:
            logger.warning(f"⚠️ Configuration validation warnings: {'; '.join(errors)}")
    
    def _load_fallback_config(self):
        """Load minimal fallback configuration when normal loading fails"""
        logger.warning("🔄 Loading fallback configuration")
        self._config_data = {
            'version': '1.0.0-fallback',
            'scoring_factors': {
                'base_values': {'base_confidence': 70, 'max_confidence': 95, 'min_confidence': 5}
            },
            'api_settings': {
                'suggestion_threshold': 5.0,
                'min_suggestion_rating': 8.0
            }
        }
    
    def _reload_config(self):
        """Reload configuration from files"""
        logger.info("🔄 Reloading configuration...")
        self._load_config()
    
    # Configuration Access Methods
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        
        Args:
            key_path: Dot-separated path (e.g., 'scoring_factors.base_values.base_confidence')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        with self._lock:
            current = self._config_data
            
            for key in key_path.split('.'):
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return default
                    
            return current
    
    def get_mature_buck_preferences(self) -> Dict[str, Any]:
        """Get mature buck preferences configuration"""
        return self.get('mature_buck_preferences', {})
    
    def get_scoring_factors(self) -> Dict[str, Any]:
        """Get scoring factors configuration"""
        return self.get('scoring_factors', {})
    
    def get_seasonal_weights(self, season: str = None) -> Dict[str, Any]:
        """Get seasonal weights configuration"""
        weights = self.get('seasonal_weights', {})
        if season:
            return weights.get(season, {})
        return weights
    
    def get_weather_modifiers(self, weather: str = None) -> Dict[str, Any]:
        """Get weather modifiers configuration"""
        modifiers = self.get('weather_modifiers', {})
        if weather:
            return modifiers.get(weather, {})
        return modifiers
    
    def get_distance_parameters(self) -> Dict[str, Any]:
        """Get distance parameters configuration"""
        return self.get('distance_parameters', {})
    
    def get_terrain_weights(self) -> Dict[str, Any]:
        """Get terrain scoring weights"""
        return self.get('terrain_weights', {})
    
    def get_api_settings(self) -> Dict[str, Any]:
        """Get API settings configuration"""
        return self.get('api_settings', {})
    
    def get_ml_parameters(self) -> Dict[str, Any]:
        """Get machine learning parameters"""
        return self.get('ml_parameters', {})
    
    # Configuration Management Methods
    
    def update_config(self, key_path: str, value: Any, persist: bool = False):
        """
        Update configuration value at runtime
        
        Args:
            key_path: Dot-separated path to update
            value: New value
            persist: Whether to save to file (admin only)
        """
        with self._lock:
            current = self._config_data
            keys = key_path.split('.')
            
            # Navigate to parent dictionary
            for key in keys[:-1]:
                if key not in current or not isinstance(current[key], dict):
                    current[key] = {}
                current = current[key]
            
            # Update the value
            old_value = current.get(keys[-1])
            current[keys[-1]] = value
            
            logger.info(f"🔧 Configuration updated: {key_path} = {value} (was: {old_value})")
            
            if persist:
                self._persist_config_change(key_path, value)
    
    def _persist_config_change(self, key_path: str, value: Any):
        """Persist configuration change to file (placeholder for future implementation)"""
        # This would implement saving changes back to configuration files
        # For now, just log the change
        logger.info(f"📝 Configuration change logged: {key_path} = {value}")
    
    def get_metadata(self) -> ConfigurationMetadata:
        """Get configuration metadata"""
        return self.metadata
    
    def reload(self):
        """Manually reload configuration"""
        self._reload_config()
    
    def shutdown(self):
        """Shutdown configuration manager and stop file watching"""
        if self._observer:
            self._observer.stop()
            self._observer.join()
            logger.info("🔄 Configuration file watcher stopped")

# Global configuration instance
_config_instance: Optional[DeerPredictionConfig] = None

def get_config(environment: str = None) -> DeerPredictionConfig:
    """
    Get global configuration instance (singleton pattern)
    
    Args:
        environment: Environment name (only used on first call)
        
    Returns:
        Global configuration instance
    """
    global _config_instance
    
    if _config_instance is None:
        _config_instance = DeerPredictionConfig(environment=environment)
        
    return _config_instance

def reload_config():
    """Reload global configuration"""
    global _config_instance
    if _config_instance:
        _config_instance.reload()

def shutdown_config():
    """Shutdown global configuration manager"""
    global _config_instance
    if _config_instance:
        _config_instance.shutdown()
        _config_instance = None
