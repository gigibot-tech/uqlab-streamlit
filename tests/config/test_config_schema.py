"""Tests for configuration schema validation."""

import pytest
from pathlib import Path
import tempfile

from uqlab.shared.config.schemas import (
    DataConfig,
    ModelConfig,
    TrainingConfig,
    EvaluationConfig,
    PathsConfig,
    ExperimentConfig,
    validate_config_dict,
)


class TestDataConfig:
    """Tests for DataConfig validation."""
    
    def test_default_config_valid(self):
        """Test that default configuration is valid."""
        config = DataConfig()
        config.validate()  # Should not raise
    
    def test_invalid_noise_type(self):
        """Test that invalid noise type raises error."""
        config = DataConfig(noise_type="invalid_noise")
        with pytest.raises(ValueError, match="Invalid noise_type"):
            config.validate()
    
    def test_negative_sample_counts(self):
        """Test that negative sample counts raise errors."""
        config = DataConfig(under_train_per_class=-1)
        with pytest.raises(ValueError, match="must be > 0"):
            config.validate()
    
    def test_random_class_format(self):
        """Test random class selection format."""
        config = DataConfig(under_supported_classes="random:3")
        config.validate()  # Should not raise
        
        config = DataConfig(under_supported_classes="random:15")
        with pytest.raises(ValueError, match="random:15"):
            config.validate()
    
    def test_comma_separated_classes(self):
        """Test comma-separated class IDs."""
        config = DataConfig(under_supported_classes="0,3,5")
        config.validate()  # Should not raise
        
        # Test invalid class ID
        config = DataConfig(under_supported_classes="0,15")
        with pytest.raises(ValueError, match="0,15"):
            config.validate()
        
        # Test duplicate class IDs
        config = DataConfig(under_supported_classes="3,3,5")
        with pytest.raises(ValueError, match="3,3,5"):
            config.validate()


class TestModelConfig:
    """Tests for ModelConfig validation."""
    
    def test_default_config_valid(self):
        """Test that default configuration is valid."""
        config = ModelConfig()
        config.validate()
    
    def test_invalid_dinov2_model(self):
        """Test that invalid model name raises error."""
        config = ModelConfig(dinov2_model="invalid")
        with pytest.raises(ValueError, match="Invalid dinov2_model"):
            config.validate()
    
    def test_invalid_dropout(self):
        """Test that invalid dropout values raise errors."""
        config = ModelConfig(dropout=-0.1)
        with pytest.raises(ValueError, match="dropout must be in"):
            config.validate()
        
        config = ModelConfig(dropout=1.5)
        with pytest.raises(ValueError, match="dropout must be in"):
            config.validate()
    
    def test_invalid_hidden_dim(self):
        """Test that invalid hidden_dim raises error."""
        config = ModelConfig(hidden_dim=0)
        with pytest.raises(ValueError, match="hidden_dim must be > 0"):
            config.validate()


class TestTrainingConfig:
    """Tests for TrainingConfig validation."""
    
    def test_default_config_valid(self):
        """Test that default configuration is valid."""
        config = TrainingConfig()
        config.validate()
    
    def test_invalid_epochs(self):
        """Test that invalid epochs raise error."""
        config = TrainingConfig(epochs=0)
        with pytest.raises(ValueError, match="epochs must be > 0"):
            config.validate()
    
    def test_invalid_learning_rate(self):
        """Test that invalid learning rate raises error."""
        config = TrainingConfig(learning_rate=-0.001)
        with pytest.raises(ValueError, match="learning_rate must be > 0"):
            config.validate()
    
    def test_invalid_batch_size(self):
        """Test that invalid batch sizes raise errors."""
        config = TrainingConfig(train_batch_size=0)
        with pytest.raises(ValueError, match="train_batch_size must be > 0"):
            config.validate()


class TestExperimentConfig:
    """Tests for complete ExperimentConfig."""
    
    def test_default_config_valid(self):
        """Test that default configuration is valid."""
        config = ExperimentConfig()
        config.validate()
    
    def test_from_dict_backward_compatible(self):
        """Test backward compatibility with dict-based configs."""
        config_dict = {
            "seed": 42,
            "device": "auto",
            "data": {
                "noise_type": "worse_label",
                "under_train_per_class": 50,
            },
            "model": {
                "dinov2_model": "small",
                "hidden_dim": 256,
            },
        }
        
        config = ExperimentConfig.from_dict(config_dict)
        config.validate()
        
        # Check values were loaded correctly
        assert config.seed == 42
        assert config.data.noise_type == "worse_label"
        assert config.model.dinov2_model == "small"
    
    def test_to_dict_roundtrip(self):
        """Test that to_dict/from_dict roundtrip works."""
        config1 = ExperimentConfig()
        config_dict = config1.to_dict()
        config2 = ExperimentConfig.from_dict(config_dict)
        
        assert config1.seed == config2.seed
        assert config1.data.noise_type == config2.data.noise_type
        assert config1.model.dinov2_model == config2.model.dinov2_model
    
    def test_yaml_roundtrip(self):
        """Test YAML save/load roundtrip."""
        config1 = ExperimentConfig()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name
        
        try:
            config1.to_yaml(temp_path)
            config2 = ExperimentConfig.from_yaml(temp_path)
            
            assert config1.seed == config2.seed
            assert config1.data.noise_type == config2.data.noise_type
        finally:
            Path(temp_path).unlink()
    
    def test_validate_config_dict_function(self):
        """Test standalone validation function for backward compatibility."""
        # Valid config
        config_dict = {
            "seed": 42,
            "data": {"noise_type": "worse_label"},
        }
        validate_config_dict(config_dict)  # Should not raise
        
        # Invalid config
        invalid_config = {
            "data": {"noise_type": "invalid_type"},
        }
        with pytest.raises(ValueError):
            validate_config_dict(invalid_config)


# Made with Bob