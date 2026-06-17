# ResNet Feature Extractor Fix - Quick Summary

## Problems Solved
1. ❌ `ValueError: ResNet feature extractor requires a pre-initialized model`
2. ❌ `AttributeError: 'ResNetFeatureExtractor' object has no attribute 'get_train_pack'`
3. ❌ `ValueError: n_passes must be >= 1, got 0`

## Root Causes

### Issue 1 & 2: ResNet Mode Handling
**ResNet in `feature_space` mode works differently than DINOv2:**
- **DINOv2**: Uses pre-computed cached features (embeddings mode)
- **ResNet**: Uses images directly but with **frozen backbone** (images mode)
- Both achieve "feature space" training, but through different mechanisms

The code was trying to use ResNet with DINOv2's workflow (cached features), but ResNet doesn't support feature caching.

### Issue 3: MC Dropout Configuration
User set `mc_passes=0` in UI, but MC Dropout requires at least 1 pass for uncertainty evaluation.

## Solutions Applied

### Fix 1: ResNet Mode Detection (Lines 908-916)
```python
# IMPORTANT: ResNet in feature_space mode works differently than DINOv2:
# - DINOv2: Uses pre-computed cached features (embeddings mode)
# - ResNet: Uses images directly but with frozen backbone (images mode)
# Both achieve "feature space" training, but through different mechanisms
if config.model.architecture == "resnet18_mcdropout" and mode == "embeddings":
    logger.info(
        "ResNet with feature_space mode: Using images with frozen backbone "
        "(ResNet doesn't support feature caching like DINOv2)"
    )
    mode = "images"  # Use images, but model will have freeze_backbone=True
```

### Fix 2: MC Dropout Validation (Lines 707-715)
```python
# Validate mc_passes - must be at least 1 for uncertainty evaluation
if mc_passes < 1:
    raise ValueError(
        f"mc_passes must be >= 1 for uncertainty quantification, got {mc_passes}. "
        f"MC Dropout requires multiple forward passes to estimate uncertainty. "
        f"Please set mc_passes to at least 1 (recommended: 10-50)."
    )
```

## Architecture Support Matrix

| Architecture | feature_space Mode | end_to_end Mode | Feature Caching | Backbone Frozen |
|--------------|-------------------|-----------------|-----------------|-----------------|
| `dinov2_mlp` | ✅ Supported | ❌ N/A | ✅ Yes | N/A (no backbone) |
| `cnn_mcdropout` | ❌ Not supported | ✅ Supported | ❌ No | ❌ No |
| `resnet18_mcdropout` | ✅ Supported* | ✅ Supported | ❌ No | ✅ Yes (feature_space) / ❌ No (end_to_end) |

*ResNet's `feature_space` mode uses images (not cached features) with frozen backbone

## How ResNet feature_space Works

1. **User selects**: ResNet + feature_space mode in UI
2. **Mode detection**: Code detects `resnet18_mcdropout` + `embeddings` mode
3. **Auto-switch**: Changes mode from `embeddings` → `images`
4. **Model building**: Creates ResNet with `freeze_backbone=True` (line 318 in factory.py)
5. **Training**: Trains only the `.fc` classifier layer, backbone stays frozen
6. **Evaluation**: MC Dropout works on the classifier for uncertainty estimation

## Expected Behavior

### ResNet + feature_space Mode:
1. ℹ️ **Info logged**: "ResNet with feature_space mode: Using images with frozen backbone"
2. ✅ **Experiment runs** using images (not cached features)
3. ✅ **Backbone frozen** - only `.fc` layer trains
4. ✅ **MC Dropout** works for uncertainty quantification
5. ✅ **Faster training** than end_to_end (fewer parameters)

### MC Dropout Configuration:
- **Minimum**: `mc_passes >= 1` (required for uncertainty)
- **Recommended**: `mc_passes = 10-50` (better uncertainty estimates)
- **Error if 0**: Clear message explaining requirement

## Files Changed
- ✅ [`scripts/run_fast_uncertainty_classification.py`](scripts/run_fast_uncertainty_classification.py)
  - Lines 707-715: MC Dropout validation
  - Lines 908-916: ResNet mode detection and switching

## Testing
- ✅ **Unit Tests**: 7/7 passing ([`test_resnet_modes_standalone.py`](test_resnet_modes_standalone.py))
- ⏳ **Runtime Testing**: Ready for verification through Streamlit UI

## How to Test
```bash
# Terminal 1: Start backend
cd uqlab-streamlit/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start Streamlit  
cd uqlab-streamlit
streamlit run streamlit_app.py

# Create ResNet experiment:
# - Architecture: ResNet18 with MC Dropout
# - Training Mode: Feature Space (frozen backbone)
# - MC Passes: Set to at least 1 (e.g., 20)
# Should run successfully!
```

## Documentation
- 📄 **Quick Summary**: [`RESNET_FIX_SUMMARY.md`](RESNET_FIX_SUMMARY.md) (this file)
- 📄 **Detailed Guide**: [`RESNET_FEATURE_EXTRACTOR_FIX.md`](RESNET_FEATURE_EXTRACTOR_FIX.md) (213 lines)

## Related Work
- ✅ Issue #1: Test ResNet Training Modes (7/7 tests passed)
- ✅ Issue #3: Verify Uncertainty Metrics (9/9 tests passed)
- ✅ Backend startup fix (comprehensive guides created)

---
**Status**: All fixes applied, ready for runtime testing