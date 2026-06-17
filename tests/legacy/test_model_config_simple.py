"""Simple test script to verify ModelConfig architecture selector functionality."""

import sys
from pathlib import Path

# Add the parent directory to the path to import config directly
sys.path.insert(0, str(Path(__file__).parent))

# Import only the config module to avoid torch dependencies
from uqlab.evaluation.classification.config import ModelConfig

def test_default_config():
    """Test default configuration."""
    config = ModelConfig()
    assert config.architecture == "dinov2_mlp"
    assert config.training_mode == "feature_space"
    assert config.dinov2_model == "dinov2_vitb14"
    assert config.hidden_dim == 256
    assert config.dropout == 0.2
    assert config.num_conv_layers == 3
    assert config.conv_channels == [32, 64, 64]
    print("✓ Default config test passed")

def test_cnn_mcdropout_config():
    """Test CNN MC Dropout configuration."""
    config = ModelConfig(
        architecture="cnn_mcdropout",
        training_mode="end_to_end",
        num_conv_layers=4,
        conv_channels=[16, 32, 64, 128]
    )
    assert config.architecture == "cnn_mcdropout"
    assert config.training_mode == "end_to_end"
    assert config.num_conv_layers == 4
    assert config.conv_channels == [16, 32, 64, 128]
    print("✓ CNN MC Dropout config test passed")

def test_resnet18_config():
    """Test ResNet18 MC Dropout configuration."""
    config = ModelConfig(
        architecture="resnet18_mcdropout",
        training_mode="end_to_end",
        hidden_dim=512,
        dropout=0.3
    )
    assert config.architecture == "resnet18_mcdropout"
    assert config.training_mode == "end_to_end"
    assert config.hidden_dim == 512
    assert config.dropout == 0.3
    print("✓ ResNet18 MC Dropout config test passed")

def test_validation_dinov2_end_to_end():
    """Test that dinov2_mlp with end_to_end mode raises error."""
    try:
        config = ModelConfig(
            architecture="dinov2_mlp",
            training_mode="end_to_end"
        )
        print("✗ Validation test failed - should have raised ValueError")
        return False
    except ValueError as e:
        assert "dinov2_mlp only supports feature_space mode" in str(e)
        print("✓ Validation test passed - correctly rejected invalid combination")
        return True

def test_validation_conv_channels_mismatch():
    """Test that mismatched conv_channels length raises error."""
    try:
        config = ModelConfig(
            architecture="cnn_mcdropout",
            num_conv_layers=3,
            conv_channels=[32, 64]  # Only 2 channels for 3 layers
        )
        print("✗ Conv channels validation test failed - should have raised ValueError")
        return False
    except ValueError as e:
        assert "conv_channels length" in str(e)
        print("✓ Conv channels validation test passed - correctly rejected mismatch")
        return True

def test_backward_compatibility():
    """Test backward compatibility with old configs."""
    # Old-style config should still work with defaults
    config = ModelConfig(
        dinov2_model="dinov2_vits14",
        hidden_dim=128,
        dropout=0.1
    )
    assert config.architecture == "dinov2_mlp"  # Default
    assert config.training_mode == "feature_space"  # Default
    assert config.dinov2_model == "dinov2_vits14"
    assert config.hidden_dim == 128
    assert config.dropout == 0.1
    print("✓ Backward compatibility test passed")

if __name__ == "__main__":
    print("Testing ModelConfig architecture selector...\n")
    try:
        test_default_config()
        test_cnn_mcdropout_config()
        test_resnet18_config()
        test_validation_dinov2_end_to_end()
        test_validation_conv_channels_mismatch()
        test_backward_compatibility()
        print("\n✅ All tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# Made with Bob
