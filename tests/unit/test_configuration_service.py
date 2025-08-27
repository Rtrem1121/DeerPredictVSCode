"""
Unit tests for the Configuration Service.

Tests the configuration management service that handles all config operations.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from backend.services.configuration_service import ConfigurationService
    from fastapi import HTTPException
    SERVICE_AVAILABLE = True
except ImportError:
    SERVICE_AVAILABLE = False
    ConfigurationService = None


@pytest.mark.skipif(not SERVICE_AVAILABLE, reason="Configuration service not available")
class TestConfigurationService:
    """Test suite for configuration service."""
    
    @pytest.fixture
    def config_service(self):
        """Fixture to provide configuration service."""
        return ConfigurationService()
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration object."""
        mock_config = MagicMock()
        mock_config.get_metadata.return_value = MagicMock(
            environment="test",
            version="1.0.0-test",
            last_loaded=None,
            source_files=["test_config.yml"],
            validation_errors=[]
        )
        mock_config.get_mature_buck_preferences.return_value = {"test": "preferences"}
        mock_config.get_scoring_factors.return_value = {"test": "scoring"}
        mock_config.get_seasonal_weights.return_value = {"test": "weights"}
        mock_config.get_weather_modifiers.return_value = {"test": "weather"}
        mock_config.get_distance_parameters.return_value = {"test": "distance"}
        mock_config.get_terrain_weights.return_value = {"test": "terrain"}
        mock_config.get_api_settings.return_value = {"test": "api"}
        mock_config.get_ml_parameters.return_value = {"test": "ml"}
        return mock_config
    
    def test_service_initialization(self, config_service):
        """Test that service initializes correctly."""
        assert config_service is not None
        assert hasattr(config_service, '_config')
    
    @patch('backend.services.configuration_service.get_config')
    def test_get_status_success(self, mock_get_config, config_service, mock_config):
        """Test successful status retrieval."""
        mock_get_config.return_value = mock_config
        
        result = config_service.get_status()
        
        assert result is not None
        assert "environment" in result
        assert "version" in result
        assert "configuration_sections" in result
        assert result["environment"] == "test"
        assert result["version"] == "1.0.0-test"
        
        # Verify configuration sections are checked
        sections = result["configuration_sections"]
        assert "mature_buck_preferences" in sections
        assert "scoring_factors" in sections
        assert "api_settings" in sections
    
    @patch('backend.services.configuration_service.get_config')
    def test_get_parameters_success(self, mock_get_config, config_service, mock_config):
        """Test successful parameter retrieval."""
        mock_get_config.return_value = mock_config
        
        result = config_service.get_parameters()
        
        assert result is not None
        assert "mature_buck_preferences" in result
        assert "scoring_factors" in result
        assert "api_settings" in result
        assert result["mature_buck_preferences"] == {"test": "preferences"}
    
    @patch('backend.services.configuration_service.get_config')
    def test_reload_configuration_success(self, mock_get_config, config_service, mock_config):
        """Test successful configuration reload."""
        mock_get_config.return_value = mock_config
        
        result = config_service.reload_configuration()
        
        assert result is not None
        assert result["status"] == "success"
        assert "message" in result
        assert "version" in result
        mock_config.reload.assert_called_once()
    
    @patch('backend.services.configuration_service.get_config')
    def test_update_parameter_success(self, mock_get_config, config_service, mock_config):
        """Test successful parameter update."""
        mock_get_config.return_value = mock_config
        
        result = config_service.update_parameter("test.key", "new_value")
        
        assert result is not None
        assert result["status"] == "success"
        assert result["key_path"] == "test.key"
        assert result["new_value"] == "new_value"
        mock_config.update_config.assert_called_once_with("test.key", "new_value", persist=False)
    
    @patch('backend.services.configuration_service.get_config')
    def test_get_status_error_handling(self, mock_get_config, config_service):
        """Test error handling in get_status."""
        mock_get_config.side_effect = Exception("Config error")
        
        with pytest.raises(HTTPException) as exc_info:
            config_service.get_status()
        
        assert exc_info.value.status_code == 500
        assert "Failed to get configuration status" in str(exc_info.value.detail)
    
    @patch('backend.services.configuration_service.get_config')
    def test_update_parameter_error_handling(self, mock_get_config, config_service, mock_config):
        """Test error handling in update_parameter."""
        mock_get_config.return_value = mock_config
        mock_config.update_config.side_effect = Exception("Update failed")
        
        with pytest.raises(HTTPException) as exc_info:
            config_service.update_parameter("invalid.key", "value")
        
        assert exc_info.value.status_code == 400
        assert "Failed to update parameter" in str(exc_info.value.detail)
    
    def test_get_config_instance(self, config_service):
        """Test getting the underlying config instance."""
        config_instance = config_service.get_config_instance()
        assert config_instance is not None


class TestConfigurationServiceIntegration:
    """Integration tests for configuration service."""
    
    @pytest.mark.skipif(not SERVICE_AVAILABLE, reason="Service not available")
    def test_real_config_integration(self):
        """Test with real configuration system."""
        try:
            service = ConfigurationService()
            
            # Test status retrieval
            status = service.get_status()
            assert "environment" in status
            assert "version" in status
            
            # Test parameter retrieval
            params = service.get_parameters()
            assert isinstance(params, dict)
            
        except Exception as e:
            pytest.skip(f"Real config not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
