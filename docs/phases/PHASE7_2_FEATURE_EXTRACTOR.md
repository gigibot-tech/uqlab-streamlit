# Phase 7.2 - Model-Agnostic Feature Extractor

## Overview

Created a unified feature extraction system that works with any model architecture (DINOv2, CNN, ResNet). This enables consistent feature extraction and caching across all architectures, making attribution signals work seamlessly with any model.

## Key Insight

Every model has "features" at some layer - we just need to extract them consistently:
- **DINOv2**: CLS token embeddings (768-dim for base model)
- **CNN**: Features before final classifier layer
- **ResNet**: Features from avgpool layer (512-dim for ResNet18, 2048-dim for ResNet50)

## Implementation

### File Created: `uq_classification/feature_extractor.py`

#### 1. Base Class: `FeatureExtractor`

Abstract base class defining the unified interface:

```python
class FeatureExtractor(ABC):
    @abstractmethod
    def extract_features(self, dataloader: DataLoader) -> torch.Tensor:
        """Extract features for entire dataset"""
        pass
    
    @abstractmethod
    def get_feature_dim(self) -> int:
        """Return feature dimensionality"""
        pass
```

#### 2. DINOv2 Implementation: `DINOv2FeatureExtractor`

Wraps the existing `EmbeddingOrganizer` for backward compatibility:

```python
class DINOv2FeatureExtractor(FeatureExtractor):
    """
    Feature extractor for DINOv2 models.
    
    Features:
    - Uses pretrained DINOv2 vision transformer
    - Extracts CLS token embeddings
    - Leverages existing caching mechanism
    - Works in feature_space training mode
    """
```

**Feature Dimensions:**
- `dinov2_vits14` (small): 384-dim
- `dinov2_vitb14` (base): 768-dim
- `dinov2_vitl14` (large): 1024-dim
- `dinov2_vitg14` (giant): 1536-dim

**Additional Methods:**
- `get_train_pack()` - Get training data with features
- `get_clean_eval_pack()` - Get clean evaluation data
- `get_aleatoric_eval_pack()` - Get aleatoric uncertainty data
- `get_epistemic_eval_pack()` - Get epistemic uncertainty data

#### 3. CNN Implementation: `CNNFeatureExtractor`

Extracts features from CNN backbone before classifier:

```python
class CNNFeatureExtractor(FeatureExtractor):
    """
    Feature extractor for custom CNN models.
    
    Architecture:
        Conv layers -> Global Average Pooling -> [Features] -> Classifier
                                                      ↑
                                              Extract here
    """
```

**Requirements:**
- Model must have either:
  - `extract_features()` method, OR
  - `features` attribute (backbone)

**Feature Extraction:**
1. Run forward pass through CNN backbone
2. Apply global average pooling if output is 4D [B, C, H, W]
3. Flatten to [B, feature_dim]

#### 4. ResNet Implementation: `ResNetFeatureExtractor`

Extracts features from ResNet avgpool layer:

```python
class ResNetFeatureExtractor(FeatureExtractor):
    """
    Feature extractor for ResNet models.
    
    Architecture:
        ResNet blocks -> AvgPool -> [Features] -> FC
                                         ↑
                                   Extract here
    """
```

**Feature Dimensions:**
- ResNet18/34: 512-dim
- ResNet50/101/152: 2048-dim

**Feature Extraction:**
1. Run through conv1 -> bn1 -> relu -> maxpool
2. Run through layer1 -> layer2 -> layer3 -> layer4
3. Apply avgpool
4. Flatten to [B, feature_dim]

#### 5. Factory Function: `create_feature_extractor()`

Automatically selects the correct extractor based on configuration:

```python
def create_feature_extractor(
    config: ModelConfig,
    device: torch.device,
    dataset: Optional[CIFAR10NDataset] = None,
    split_spec: Optional[SplitSpec] = None,
    feature_cache_dir: Optional[Path] = None,
    noise_type: Optional[str] = None,
    batch_size: int = 64,
    model: Optional[nn.Module] = None,
) -> FeatureExtractor:
    """Factory function to create appropriate feature extractor"""
```

## Usage Examples

### Example 1: DINOv2 Feature Extraction

```python
from uq_classification import create_feature_extractor
from uq_classification.config import ModelConfig

# Create config
config = ModelConfig(
    architecture="dinov2_mlp",
    training_mode="feature_space",
    dinov2_model="dinov2_vitb14"
)

# Create extractor
extractor = create_feature_extractor(
    config=config,
    device=device,
    dataset=cifar10n_dataset,
    split_spec=split_spec,
    feature_cache_dir=Path("./cache"),
    noise_type="worse_label",
)

# Extract features (uses caching)
extractor.organizer.load_or_compute_features()
train_pack = extractor.get_train_pack()
print(f"Features shape: {train_pack['features'].shape}")  # [N, 768]
print(f"Feature dim: {extractor.get_feature_dim()}")  # 768
```

### Example 2: CNN Feature Extraction

```python
from uq_classification import create_feature_extractor, CNNFeatureExtractor
from torch.utils.data import DataLoader

# Assume you have a CNN model
cnn_model = create_cnn_model(...)

# Create extractor
extractor = create_feature_extractor(
    config=config,
    device=device,
    model=cnn_model,
)

# Extract features
dataloader = DataLoader(dataset, batch_size=64)
features = extractor.extract_features(dataloader)
print(f"Features shape: {features.shape}")  # [N, feature_dim]
print(f"Feature dim: {extractor.get_feature_dim()}")
```

### Example 3: ResNet Feature Extraction

```python
import torchvision.models as models
from uq_classification import create_feature_extractor

# Create ResNet18
resnet = models.resnet18(pretrained=True)

# Create config
config = ModelConfig(
    architecture="resnet18_mcdropout",
    training_mode="end_to_end"
)

# Create extractor
extractor = create_feature_extractor(
    config=config,
    device=device,
    model=resnet,
)

# Extract features
features = extractor.extract_features(dataloader)
print(f"Features shape: {features.shape}")  # [N, 512]
print(f"Feature dim: {extractor.get_feature_dim()}")  # 512
```

### Example 4: Direct Instantiation

```python
from uq_classification import DINOv2FeatureExtractor, CNNFeatureExtractor, ResNetFeatureExtractor

# DINOv2
dinov2_extractor = DINOv2FeatureExtractor(
    dataset=dataset,
    split_spec=split_spec,
    feature_cache_dir=Path("./cache"),
    noise_type="worse_label",
    dinov2_model="dinov2_vitb14",
    batch_size=256,
    device=device,
)

# CNN
cnn_extractor = CNNFeatureExtractor(
    model=cnn_model,
    device=device,
    batch_size=64,
)

# ResNet
resnet_extractor = ResNetFeatureExtractor(
    model=resnet_model,
    device=device,
    batch_size=64,
)
```

## Benefits

### ✅ Unified Interface
- All architectures implement the same `FeatureExtractor` interface
- Consistent API across DINOv2, CNN, and ResNet
- Easy to swap architectures without code changes

### ✅ Consistent Caching
- DINOv2 uses existing caching mechanism
- CNN/ResNet can leverage same caching strategy
- Reduces redundant computation

### ✅ Easy Extension
- Add new architectures by implementing `FeatureExtractor`
- No changes to downstream code (attribution, evaluation)
- Modular and maintainable

### ✅ Attribution Compatibility
- Attribution signals work with any features
- DualXDA can use CNN/ResNet features
- Enables end-to-end uncertainty analysis

## Integration with Existing Code

### Backward Compatibility

The `DINOv2FeatureExtractor` wraps `EmbeddingOrganizer`, so existing code continues to work:

```python
# Old way (still works)
organizer = EmbeddingOrganizer(...)
organizer.load_or_compute_features()
train_pack = organizer.get_train_pack()

# New way (unified interface)
extractor = DINOv2FeatureExtractor(...)
extractor.organizer.load_or_compute_features()
train_pack = extractor.get_train_pack()
```

### Updated Exports

Added to `uq_classification/__init__.py`:

```python
from .feature_extractor import (
    FeatureExtractor,
    DINOv2FeatureExtractor,
    CNNFeatureExtractor,
    ResNetFeatureExtractor,
    create_feature_extractor,
)
```

## Architecture-Specific Notes

### DINOv2 (feature_space mode)
- ✅ Pretrained on ImageNet
- ✅ High-quality features out-of-the-box
- ✅ Existing caching mechanism
- ✅ Fast training (only MLP head)
- ⚠️ Requires transformers library
- ⚠️ Only supports feature_space mode

### CNN (end_to_end mode)
- ✅ Lightweight and fast
- ✅ Trainable from scratch
- ✅ Flexible architecture
- ✅ Good for small datasets
- ⚠️ Requires end_to_end training
- ⚠️ May need more epochs

### ResNet (end_to_end mode)
- ✅ Can use pretrained weights
- ✅ Strong baseline performance
- ✅ Well-studied architecture
- ✅ Good feature representations
- ⚠️ Larger model (more parameters)
- ⚠️ Requires end_to_end training

## Testing

### Manual Testing

```python
# Test DINOv2 extractor
config = ModelConfig(architecture="dinov2_mlp")
extractor = create_feature_extractor(config, device, dataset=dataset, ...)
assert extractor.get_feature_dim() == 768  # For base model

# Test CNN extractor
config = ModelConfig(architecture="cnn_mcdropout")
extractor = create_feature_extractor(config, device, model=cnn_model)
features = extractor.extract_features(dataloader)
assert features.shape[1] == extractor.get_feature_dim()

# Test ResNet extractor
config = ModelConfig(architecture="resnet18_mcdropout")
extractor = create_feature_extractor(config, device, model=resnet_model)
assert extractor.get_feature_dim() == 512  # ResNet18
```

### Integration Testing

```python
# Test with attribution signals
from uq_classification import compute_attribution_structure_signals

# Extract features
extractor = create_feature_extractor(config, device, ...)
features = extractor.extract_features(dataloader)

# Compute attribution signals (should work with any features)
signals = compute_attribution_structure_signals(
    features=features,
    labels=labels,
    ...
)
```

## Next Steps

This feature extractor enables:

1. **Phase 7.3**: Implement CNN MC Dropout model class
   - Create `CNNMCDropout` model
   - Add `extract_features()` method
   - Integrate with feature extractor

2. **Phase 7.4**: Implement ResNet18 MC Dropout model class
   - Create `ResNet18MCDropout` model
   - Add `extract_features()` method
   - Integrate with feature extractor

3. **Phase 7.5**: Update training pipeline
   - Handle different training modes (feature_space vs end_to_end)
   - Use feature extractor for attribution signals
   - Support all architectures

4. **Phase 7.6**: Add architecture-specific data loaders
   - Raw image loaders for end_to_end training
   - Feature loaders for feature_space training
   - Unified interface

## Files Modified

### Created
- `walaris-cen/uq_classification/feature_extractor.py` (485 lines)
  - `FeatureExtractor` base class
  - `DINOv2FeatureExtractor` implementation
  - `CNNFeatureExtractor` implementation
  - `ResNetFeatureExtractor` implementation
  - `create_feature_extractor()` factory function

### Modified
- `walaris-cen/uq_classification/__init__.py`
  - Added feature extractor imports
  - Updated `__all__` exports
  - Bumped version to 2.3.0
  - Added documentation reference

### Documentation
- `walaris-cen/PHASE7_2_FEATURE_EXTRACTOR.md` (this file)

## Summary

✅ **Base class created** - `FeatureExtractor` with unified interface  
✅ **DINOv2 implementation** - Wraps existing `EmbeddingOrganizer`  
✅ **CNN implementation** - Extracts from backbone before classifier  
✅ **ResNet implementation** - Extracts from avgpool layer  
✅ **Factory function** - Automatic extractor selection  
✅ **Backward compatible** - Existing code continues to work  
✅ **Well documented** - Comprehensive docstrings and examples  
✅ **Exported** - Available via `uq_classification` package  

The feature extraction system is now architecture-agnostic and ready for use with any model!

---

**Made with Bob - Phase 7.2 Complete** ✨