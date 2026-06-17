# Phase 7.3: Model Factory Implementation

## Overview

Created a unified model factory (`uq_classification/model_factory.py`) that instantiates the correct model architecture based on configuration, including CNN and ResNet18 with MC Dropout support.

## Implementation Summary

### 1. Model Architectures

All three architectures implement the standard interface:

```python
class UncertaintyModel(nn.Module):
    def forward(self, x) -> torch.Tensor:
        """Returns logits [B, C]"""
    
    def mc_forward(self, x, n_passes: int) -> torch.Tensor:
        """Returns probabilities [T, B, C] with MC dropout"""
    
    def extract_features(self, x) -> torch.Tensor:
        """Returns features [B, D] for attribution (CNN/ResNet only)"""
```

#### A. EmbeddingDropoutMLP (DINOv2 + MLP)
- **Location**: `uq_classification/models.py` (already exists)
- **Mode**: Feature space training
- **Input**: Pre-extracted DINOv2 embeddings [B, 768]
- **Architecture**: Dropout → Linear(768→256) → ReLU → Dropout → Linear(256→10)
- **Features**: Works with cached embeddings, fast training

#### B. CNNMCDropout (New)
- **Location**: `uq_classification/model_factory.py`
- **Mode**: End-to-end training
- **Input**: Raw images [B, 3, 32, 32]
- **Architecture**: 
  - Conv32 (3→32) + BN + Pool
  - Conv64 (32→64) + BN + Pool
  - Conv64 (64→64) + BN + Pool
  - FC128 (1024→128) [Feature extraction point]
  - Dropout
  - Classifier (128→10)
- **Features**: 
  - Based on Gaussian Logits architecture
  - Extract features from FC128 for attribution
  - Compatible with DualXDA

#### C. ResNet18MCDropout (New)
- **Location**: `uq_classification/model_factory.py`
- **Mode**: End-to-end training
- **Input**: Raw images [B, 3, 32, 32]
- **Architecture**:
  - ResNet18 backbone (torchvision)
  - AvgPool → [Feature extraction point: 512-dim]
  - Dropout
  - Classifier (512→10)
- **Features**:
  - Optional ImageNet pretrained weights
  - Extract features from avgpool layer
  - Compatible with DualXDA

### 2. Factory Function

```python
def build_model(
    config: ModelConfig,
    num_classes: int,
    feature_dim: Optional[int] = None
) -> nn.Module:
    """
    Build model based on architecture config.
    
    Args:
        config: Model configuration with architecture selection
        num_classes: Number of output classes
        feature_dim: Feature dimensionality (for feature-space models)
    
    Returns:
        Model implementing forward() and mc_forward()
    """
```

**Supported Architectures**:
- `dinov2_mlp`: DINOv2 + MLP (requires `feature_dim`)
- `cnn_mcdropout`: CNN with MC Dropout
- `resnet18_mcdropout`: ResNet18 with MC Dropout

### 3. Integration Points

#### With Feature Extractor (Phase 7.2)
```python
from uq_classification.model_factory import build_model
from uq_classification.feature_extractor import create_feature_extractor

# Build model
model = build_model(config, num_classes=10)

# Create feature extractor for the model
extractor = create_feature_extractor(
    config=config,
    device=device,
    model=model,  # Pass model for CNN/ResNet
)

# Extract features for attribution
features = extractor.extract_features(dataloader)
```

#### With DualXDA Attribution
All models have identifiable classifier layers:
- **DINOv2 MLP**: `model.fc` (final linear layer)
- **CNN**: `model.classifier` (final linear layer)
- **ResNet18**: `model.classifier` (final linear layer)

This enables DualXDA to compute attribution signals.

### 4. Configuration Examples

#### DINOv2 + MLP (Feature Space)
```yaml
model:
  architecture: dinov2_mlp
  training_mode: feature_space
  dinov2_model: dinov2_vitb14
  hidden_dim: 256
  dropout: 0.2
```

#### CNN MC Dropout (End-to-End)
```yaml
model:
  architecture: cnn_mcdropout
  training_mode: end_to_end
  dropout: 0.3
```

#### ResNet18 MC Dropout (End-to-End)
```yaml
model:
  architecture: resnet18_mcdropout
  training_mode: end_to_end
  dropout: 0.3
  use_untrained_resnet: false  # Use ImageNet pretrained
```

### 5. Usage Examples

#### Basic Usage
```python
from uq_classification.config import ModelConfig
from uq_classification.model_factory import build_model

# Create config
config = ModelConfig(
    architecture="cnn_mcdropout",
    training_mode="end_to_end",
    dropout=0.3,
)

# Build model
model = build_model(config, num_classes=10)

# Standard forward pass
images = torch.randn(4, 3, 32, 32)
logits = model(images)  # [4, 10]

# MC Dropout forward pass
mc_probs = model.mc_forward(images, n_passes=20)  # [20, 4, 10]

# Extract features (for CNN/ResNet)
features = model.extract_features(images)  # [4, 128] for CNN, [4, 512] for ResNet
```

#### Convenience Functions
```python
from uq_classification.model_factory import (
    build_dinov2_mlp,
    build_cnn_mcdropout,
    build_resnet18_mcdropout,
)

# Direct instantiation
model1 = build_dinov2_mlp(feature_dim=768, num_classes=10)
model2 = build_cnn_mcdropout(num_classes=10, dropout=0.3)
model3 = build_resnet18_mcdropout(num_classes=10, pretrained=True)
```

### 6. Key Design Decisions

#### MC Dropout Implementation
All models use the same MC Dropout pattern:
1. Set model to eval mode: `model.eval()`
2. Enable dropout layers: `model.enable_dropout()`
3. Perform multiple forward passes with dropout active
4. Return stacked softmax probabilities [T, B, C]

#### Feature Extraction
- **DINOv2**: Features come from pretrained backbone (handled by EmbeddingOrganizer)
- **CNN**: Features extracted from FC128 layer (before dropout)
- **ResNet18**: Features extracted from avgpool layer (before dropout)

This ensures features are meaningful representations before the stochastic dropout layer.

#### Classifier Layer Identification
All models expose their classifier as `model.classifier` (or `model.fc` for DINOv2 MLP), making it easy for DualXDA to identify the layer for attribution computation.

### 7. Testing

The module includes a `__main__` block that tests all three architectures:

```bash
python -m uq_classification.model_factory
```

Expected output:
```
Testing Model Factory
==================================================

1. DINOv2 + MLP (feature space)
   Model: EmbeddingDropoutMLP
   Forward: torch.Size([4, 768]) -> torch.Size([4, 10])
   MC Forward: torch.Size([4, 768]) -> torch.Size([5, 4, 10])

2. CNN MC Dropout (end-to-end)
   Model: CNNMCDropout
   Forward: torch.Size([4, 3, 32, 32]) -> torch.Size([4, 10])
   Features: torch.Size([4, 3, 32, 32]) -> torch.Size([4, 128])
   MC Forward: torch.Size([4, 3, 32, 32]) -> torch.Size([5, 4, 10])

3. ResNet18 MC Dropout (end-to-end)
   Model: ResNet18MCDropout
   Forward: torch.Size([4, 3, 32, 32]) -> torch.Size([4, 10])
   Features: torch.Size([4, 3, 32, 32]) -> torch.Size([4, 512])
   MC Forward: torch.Size([4, 3, 32, 32]) -> torch.Size([5, 4, 10])

==================================================
All tests passed! ✓
```

### 8. Files Created

- `uqlab-streamlit/uq_classification/model_factory.py` (467 lines)
  - `CNNMCDropout` class
  - `ResNet18MCDropout` class
  - `build_model()` factory function
  - Convenience builder functions
  - Test suite in `__main__`

### 9. Next Steps

The model factory is now ready for integration with:
1. **Training Pipeline**: Use `build_model()` to instantiate models
2. **Feature Extraction**: Works with `create_feature_extractor()` from Phase 7.2
3. **Attribution Signals**: All models expose classifier layers for DualXDA
4. **Uncertainty Estimation**: All models implement `mc_forward()` for MC Dropout

### 10. Validation Checklist

✅ All three architectures implemented
✅ Unified interface (forward, mc_forward, extract_features)
✅ Factory function with config-based selection
✅ Integration with existing EmbeddingDropoutMLP
✅ CNN based on Gaussian Logits architecture
✅ ResNet18 with torchvision backbone
✅ MC Dropout capability for all models
✅ Feature extraction for attribution
✅ Compatible with DualXDA (identifiable classifier)
✅ Comprehensive documentation
✅ Test suite included

## Conclusion

Phase 7.3 is complete. The model factory provides a clean, unified interface for creating uncertainty-aware models across three different architectures, all implementing the same standard interface for training, inference, and uncertainty estimation.