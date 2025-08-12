import pytest
import os
from backend.config_manager import DeerPredictionConfig

@pytest.fixture
def config_manager(tmp_path):
    """Provides a DeerPredictionConfig instance with a temporary config directory."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "defaults.yaml").write_text("deer_prediction_config:\n  version: 1.0.0")
    return DeerPredictionConfig(config_dir=str(config_dir))

class TestConfigManager:
    def test_apply_env_overrides(self, config_manager):
        """Test that environment variable overrides are applied correctly."""
        os.environ["DEER_PRED_SCORING_FACTORS_BASE_VALUES_BASE_CONFIDENCE"] = "80"
        config = config_manager._apply_env_overrides({'deer_prediction_config': {}})
        assert config['deer_prediction_config']['scoring_factors']['base_values']['base_confidence'] == 80
        del os.environ["DEER_PRED_SCORING_FACTORS_BASE_VALUES_BASE_CONFIDENCE"]
