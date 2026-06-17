# ResNet Feature Extractor Runtime Error - Fix Documentation

## Problem Summary

**Error**: `ValueError: ResNet feature extractor requires a pre-initialized model`

**Location**: [`feature_extractors.py:478`](src/uqlab/2_models/feature_extractors.py:478)

**Trigger**: Running ResNet experiments with `feature_space` training mode through the Streamlit UI

## Root Cause Analysis

### The Issue
In [`run_fast_uncertainty_classification.py`](scripts/run_fast_uncertainty_classification.py), the code had an incorrect execution order:

1. **Line 902**: Called `create_feature_extractor()` WITHOUT the `model` parameter
2. **Line 949**: Built the model AFTER creating the feature extractor
3. **Line 957**: Second call to `create_feature_extractor()` WITH model (for images mode only)

### Why This Failed
The [`ResNetFeatureExtractor`](src/uqlab/2_models/feature_extractors.py:480-484) requires a pre-initialized PyTorch model because:
- ResNet uses the actual model's forward pass for feature extraction
- Unlike DINOv2 which uses a separate pretrained model, ResNet needs the classifier model itself
- The feature extractor wraps the model to extract intermediate features

### Architecture-Specific Behavior

| Architecture | Training Mode | Requires Model? | Feature Source |
|--------------|---------------|-----------------|----------------|
| `dinov2_mlp` | `feature_space` | ❌ No | Pretrained DINOv2 |
| `cnn_mcdropout` | `end_to_end` | ✅ Yes | CNN backbone |
| `resnet18_mcdropout` | `feature_space` | ✅ Yes | ResNet backbone |
| `resnet18_mcdropout` | `end_to_end` | ✅ Yes | ResNet backbone |

## The Fix

### Changes Made to `run_fast_uncertainty_classification.py`

#### 1. Early Model Building for ResNet (Lines 901-909)
```python
# For ResNet in feature_space mode, we need to build the model first
# because ResNetFeatureExtractor requires a pre-initialized model
model_for_feature_extractor = None
if mode == "embeddings" and config.model.architecture == "resnet18_mcdropout":
    model_for_feature_extractor = build_model(
        config=config.model,
        num_classes=10,
        feature_dim=None,  # ResNet doesn't use feature_dim
    )
    model_for_feature_extractor = model_for_feature_extractor.to(device)
```

**Why**: Build the model BEFORE creating the feature extractor for ResNet in feature_space mode.

#### 2. Pass Model to Feature Extractor (Line 922)
```python
feature_extractor = create_feature_extractor(
    config.model,
    device=device,
    dataset=dataset,
    split_spec=split_spec,
    feature_cache_dir=feature_cache_dir,
    noise_type=noise_type,
    batch_size=feature_batch_size,
    model=model_for_feature_extractor,  # Pass model for ResNet
)
```

**Why**: Provide the pre-built model to the feature extractor creation function.

#### 3. Conditional Feature Caching (Lines 924-931)
```python
# Only DINOv2 uses the feature organizer for caching
if isinstance(feature_extractor, DINOv2FeatureExtractor):
    feature_extractor.organizer.load_or_compute_features()
elif config.model.architecture != "resnet18_mcdropout":
    raise TypeError(
        f"Unexpected feature extractor type for architecture {config.model.architecture}. "
        f"Expected DINOv2FeatureExtractor or ResNetFeatureExtractor."
    )
```

**Why**: Only DINOv2 has a feature organizer for caching. ResNet extracts features on-the-fly.

#### 4. Model Reuse (Lines 966-974)
```python
# Reuse model if already built for ResNet feature extractor, otherwise build new
if model_for_feature_extractor is not None:
    model = model_for_feature_extractor
else:
    model = build_model(
        config=config.model,
        num_classes=10,
        feature_dim=feature_dim if mode == "embeddings" else None,
    )
    model = model.to(device)
```

**Why**: Avoid rebuilding the model if we already created it for the feature extractor.

## Execution Flow After Fix

### For ResNet with `feature_space` Mode:
```
1. Determine mode = "embeddings" (feature_space → embeddings)
2. Build ResNet model early (lines 901-909)
3. Create ResNetFeatureExtractor with model (lines 914-922)
4. Skip feature caching (ResNet doesn't cache)
5. Load training/eval data
6. Reuse the pre-built model (lines 966-974)
7. Train the model
8. Evaluate with uncertainty quantification
```

### For DINOv2 with `feature_space` Mode:
```
1. Determine mode = "embeddings"
2. model_for_feature_extractor = None (not ResNet)
3. Create DINOv2FeatureExtractor without model
4. Load or compute cached features
5. Load training/eval data
6. Build new classifier model (lines 966-974)
7. Train the classifier on cached features
8. Evaluate with uncertainty quantification
```

### For Any Architecture with `end_to_end` Mode:
```
1. Determine mode = "images"
2. model_for_feature_extractor = None (not in embeddings mode)
3. Load image datasets directly
4. Build model (lines 966-974)
5. Create feature extractor with model (lines 977-983)
6. Train the full model end-to-end
7. Evaluate with uncertainty quantification
```

## Testing

### Unit Tests (Already Passing)
- ✅ [`test_resnet_modes_standalone.py`](test_resnet_modes_standalone.py): 7/7 tests passed
  - Tests ResNet feature_space and end_to_end modes
  - Validates freeze_backbone functionality
  - Confirms MC Dropout works in both modes

### Runtime Testing Required
To verify the fix works in production:

```bash
# 1. Start the backend
cd uqlab-streamlit/backend
./start_backend.sh

# 2. In another terminal, start Streamlit
cd uqlab-streamlit
streamlit run streamlit_app.py

# 3. Create an experiment with:
#    - Architecture: ResNet18 with MC Dropout
#    - Training Mode: Feature Space (freeze backbone)
#    - Submit and verify it runs without errors
```

## Related Files

### Modified
- [`scripts/run_fast_uncertainty_classification.py`](scripts/run_fast_uncertainty_classification.py) - Main fix location

### Referenced (No Changes)
- [`src/uqlab/2_models/feature_extractors.py`](src/uqlab/2_models/feature_extractors.py) - Feature extractor implementations
- [`src/uqlab/2_models/model_builder.py`](src/uqlab/2_models/model_builder.py) - Model building logic
- [`test_resnet_modes_standalone.py`](test_resnet_modes_standalone.py) - Unit tests (all passing)

## Key Takeaways

1. **Architecture Matters**: Different architectures have different requirements for feature extraction
2. **Execution Order**: Model must be built BEFORE creating ResNet feature extractors
3. **Mode-Specific Logic**: Feature caching only applies to DINOv2, not ResNet
4. **Model Reuse**: Avoid rebuilding models unnecessarily for efficiency

## Status

✅ **Fix Applied**: All changes implemented in `run_fast_uncertainty_classification.py`
⏳ **Testing Needed**: Runtime testing through Streamlit UI required
📋 **Documentation**: This comprehensive guide created

---

**Related Issues**:
- Issue #1: Test ResNet Training Modes ✅ COMPLETE (7/7 tests passed)
- Issue #3: Verify Uncertainty Metrics ✅ COMPLETE (9/9 tests passed)

**Next Steps**:
1. Test the fix by running a ResNet experiment through Streamlit UI
2. Verify no errors occur during training and evaluation
3. Confirm uncertainty metrics are calculated correctly
4. Update GitHub issues if needed