# Phase 7.1 - Architecture Selector Implementation

## Overview

Updated `uq_classification/config.py` to support multiple model architectures through a flexible configuration system.

## Changes Made

### 1. ModelConfig Class Transformation

**Before:** Simple dataclass with fixed DINOv2 architecture
**After:** Pydantic BaseModel with architecture selection and validation

### 2. New Fields Added

#### Architecture Selection
- `architecture`: Choose between:
  - `"dinov2_mlp"` (default) - DINOv2 with MLP head
  - `"cnn_mcdropout"` - Custom CNN with MC Dropout
  - `"resnet18_mcdropout"` - ResNet18 with MC Dropout

- `training_mode`: Choose between:
  - `"feature_space"` (default) - Train on precomputed embeddings
  - `"end_to_end"` - Train on raw images

#### Architecture-Specific Fields

**DINOv2-specific** (only used when `architecture="dinov2_mlp"`):
- `dinov2_model`: Model variant (default: "dinov2_vitb14")

**CNN-specific** (only used when `architecture="cnn_mcdropout"`):
- `num_conv_layers`: Number of convolutional layers (default: 3)
- `conv_channels`: List of channel sizes (default: [32, 64, 64])

**Common parameters** (used by all architectures):
- `hidden_dim`: Hidden layer dimension (default: 256)
- `dropout`: Dropout rate (default: 0.2)
- `use_untrained_resnet`: Use untrained ResNet-50 (default: False)

### 3. Validation Rules

#### Training Mode Validation
```python
@field_validator("training_mode")
def validate_training_mode(cls, v, info):
    arch = info.data.get("architecture")
    if arch == "dinov2_mlp" and v != "feature_space":
        raise ValueError("dinov2_mlp only supports feature_space mode")
    return v
```

**Rule:** DINOv2 architecture only supports feature_space training mode.

#### Conv Channels Validation
```python
@field_validator("conv_channels")
def validate_conv_channels(cls, v, info):
    num_layers = info.data.get("num_conv_layers", 3)
    if len(v) != num_layers:
        raise ValueError(
            f"conv_channels length ({len(v)}) must match num_conv_layers ({num_layers})"
        )
    return v
```

**Rule:** Length of `conv_channels` must match `num_conv_layers`.

### 4. YAML Configuration Support

Updated `ExperimentConfig.from_yaml()` to parse new fields:

```python
model_config = ModelConfig(
    architecture=model_dict.get("architecture", "dinov2_mlp"),
    training_mode=model_dict.get("training_mode", "feature_space"),
    dinov2_model=model_dict.get("dinov2_model", "dinov2_vitb14"),
    hidden_dim=model_dict.get("hidden_dim", 256),
    dropout=model_dict.get("dropout", 0.2),
    use_untrained_resnet=model_dict.get("use_untrained_resnet", False),
    num_conv_layers=model_dict.get("num_conv_layers", 3),
    conv_channels=conv_channels,
)
```

Supports both list and comma-separated string formats for `conv_channels`.

## Usage Examples

### Example 1: Default DINOv2 Configuration (Backward Compatible)

```yaml
model:
  dinov2_model: dinov2_vitb14
  hidden_dim: 256
  dropout: 0.2
```

This automatically uses:
- `architecture: dinov2_mlp`
- `training_mode: feature_space`

### Example 2: CNN MC Dropout

```yaml
model:
  architecture: cnn_mcdropout
  training_mode: end_to_end
  num_conv_layers: 3
  conv_channels: "32,64,64"
  hidden_dim: 256
  dropout: 0.2
```

### Example 3: ResNet18 MC Dropout

```yaml
model:
  architecture: resnet18_mcdropout
  training_mode: end_to_end
  hidden_dim: 512
  dropout: 0.3
```

### Example 4: Programmatic Usage

```python
from uq_classification.config import ModelConfig

# Default DINOv2
config1 = ModelConfig()

# CNN MC Dropout
config2 = ModelConfig(
    architecture="cnn_mcdropout",
    training_mode="end_to_end",
    num_conv_layers=4,
    conv_channels=[16, 32, 64, 128]
)

# ResNet18 MC Dropout
config3 = ModelConfig(
    architecture="resnet18_mcdropout",
    training_mode="end_to_end",
    hidden_dim=512,
    dropout=0.3
)
```

## Backward Compatibility

✅ **Fully backward compatible** with existing configurations:

1. All existing YAML configs will work without modification
2. Default values match previous behavior
3. Optional fields allow gradual migration
4. Type hints updated to use `Optional` where needed

## Validation Examples

### Valid Configurations

✅ DINOv2 with feature_space (default)
```python
ModelConfig(architecture="dinov2_mlp", training_mode="feature_space")
```

✅ CNN with end_to_end
```python
ModelConfig(architecture="cnn_mcdropout", training_mode="end_to_end")
```

✅ ResNet18 with end_to_end
```python
ModelConfig(architecture="resnet18_mcdropout", training_mode="end_to_end")
```

### Invalid Configurations

❌ DINOv2 with end_to_end
```python
ModelConfig(architecture="dinov2_mlp", training_mode="end_to_end")
# Raises: ValueError: dinov2_mlp only supports feature_space mode
```

❌ Mismatched conv_channels
```python
ModelConfig(
    architecture="cnn_mcdropout",
    num_conv_layers=3,
    conv_channels=[32, 64]  # Only 2 channels for 3 layers
)
# Raises: ValueError: conv_channels length (2) must match num_conv_layers (3)
```

## Testing

Run validation script:
```bash
cd uqlab-streamlit
python3 validate_config_changes.py
```

## Example Configuration Files

Created example YAML files demonstrating each architecture:

1. `configs/example_cnn_mcdropout.yaml` - CNN MC Dropout configuration
2. `configs/example_resnet18_mcdropout.yaml` - ResNet18 MC Dropout configuration

## Next Steps

This configuration update enables:

1. **Phase 7.2**: Implement CNN MC Dropout model class
2. **Phase 7.3**: Implement ResNet18 MC Dropout model class
3. **Phase 7.4**: Update training pipeline to handle different architectures
4. **Phase 7.5**: Add architecture-specific data loaders for end-to-end training

## Technical Details

### Dependencies Added
- `pydantic`: For BaseModel and field validation
- `typing.Literal`: For type-safe architecture selection

### Files Modified
- `uqlab-streamlit/uq_classification/config.py`: Main configuration file

### Files Created
- `uqlab-streamlit/configs/example_cnn_mcdropout.yaml`: Example CNN config
- `uqlab-streamlit/configs/example_resnet18_mcdropout.yaml`: Example ResNet18 config
- `uqlab-streamlit/validate_config_changes.py`: Validation script
- `uqlab-streamlit/PHASE7_1_ARCHITECTURE_SELECTOR.md`: This documentation

## Summary

✅ Architecture selector implemented with 3 options
✅ Training mode selector (feature_space vs end_to_end)
✅ Architecture-specific fields added
✅ Validation rules enforced
✅ YAML parsing updated
✅ Backward compatibility maintained
✅ Example configurations provided
✅ Documentation complete