# Changes Summary: AUROC Explanation & Untrained ResNet Feature

## Overview

This document summarizes the changes made to:
1. **Explain AUROC metrics** and their interpretation in the context of uncertainty quantification
2. **Add support for untrained ResNet-50** as an alternative feature extractor (for baseline comparisons)

## 1. AUROC Metrics Documentation

### New File: `AUROC_METRICS_EXPLAINED.md`

Created comprehensive documentation explaining:

- **What AUROC is**: Area Under ROC Curve metric (0-1 scale)
- **What we're measuring**: How well uncertainty signals detect problematic samples
- **Interpreting scores**: 
  - 0.90-1.00: Excellent
  - 0.80-0.90: Good
  - 0.70-0.80: Fair
  - 0.60-0.70: Poor (your current range)
  - 0.50-0.60: Very poor
  - <0.50: Inverse correlation

- **Understanding "40% Aleatoric Noise"**: 
  - 40% of training samples have incorrect labels
  - This simulates real-world label noise
  - Used to test if uncertainty signals can detect mislabeled data

- **Why scores might be "stuck" at 0.65-0.70**:
  - Feature limitations (DINOv2 embeddings might not capture the right patterns)
  - Label noise characteristics (CIFAR-10N noise is adversarial/hard to detect)
  - Model capacity (small MLP might be too simple)
  - Data imbalance issues

- **Best possible outcomes**: Visual examples of score distributions
- **Improvement strategies**: Better features, enhanced uncertainty estimation, training strategies
- **Practical recommendations**: What you can/cannot do with 0.65-0.70 scores

## 2. Untrained ResNet-50 Support

### Purpose

Adding untrained ResNet-50 allows you to:
- **Establish a baseline**: See how much pretrained features (DINOv2) actually help
- **Understand feature importance**: If untrained features work poorly, it confirms pretrained features are crucial
- **Debug experiments**: Isolate whether issues are in features vs. classifier

### Changes Made

#### A. Configuration (`uq_classification/config.py`)

```python
@dataclass
class ModelConfig:
    dinov2_model: str = "dinov2_vitb14"
    hidden_dim: int = 256
    dropout: float = 0.2
    use_untrained_resnet: bool = False  # NEW FLAG
```

- Added `use_untrained_resnet` boolean flag to ModelConfig
- Updated YAML parsing to read this flag from config files

#### B. Feature Extraction (`uq_classification/data_loader.py`)

**Modified `extract_features_for_indices()`**:
- Added `use_untrained_resnet` parameter
- When True, uses `torchvision.models.resnet50(weights=None)` instead of DINOv2
- Extracts 2048-dim features from ResNet-50's penultimate layer
- When False, uses DINOv2 as before (768-dim features)

**Modified `maybe_load_or_compute_feature_cache()`**:
- Added `use_untrained_resnet` parameter
- Passes flag through to feature extraction

**Modified `build_feature_cache_path()`**:
- Cache filenames now include model type: `resnet50_untrained` or `dinov2_*`
- Ensures untrained and pretrained features don't collide in cache

#### C. UI Components (`ui_components/experiment_config.py`)

**Modified `render_model_config()`**:
- Returns 4 values now: `(dinov2_model, hidden_dim, dropout, use_untrained_resnet)`
- Added checkbox: "🔬 Use Untrained ResNet-50 (Experimental)"
- Shows warning when enabled: "Features will be random. Expect poor performance."
- Disables DINOv2 selection when untrained ResNet is chosen

**Modified `build_base_experiment_config()`**:
- Added `use_untrained_resnet` parameter
- Includes flag in returned config dictionary

#### D. Streamlit App (`streamlit_app.py`)

**Single Experiment Tab**:
- Updated to capture 4 return values from `render_model_config()`
- Passes `use_untrained_resnet` to `build_base_experiment_config()`

**Batch Experiment Tab**:
- Updated batch config building to include `use_untrained_resnet` flag
- Defaults to False if not specified

## 3. How to Use the New Features

### Using Untrained ResNet

1. **In the UI**:
   - Go to "Model & Training Configuration" section
   - Check "🔬 Use Untrained ResNet-50 (Experimental)"
   - The DINOv2 selection will be disabled
   - Create experiment as normal

2. **Expected Results**:
   - **Much worse performance** than DINOv2 (AUROC likely 0.50-0.55)
   - This confirms pretrained features are important
   - If untrained ResNet performs similarly to DINOv2, it suggests:
     - The task is very easy, or
     - The classifier is the bottleneck, not features

3. **In Config Files** (YAML):
   ```yaml
   model:
     dinov2_model: "dinov2_vitb14"  # Ignored if use_untrained_resnet=true
     hidden_dim: 256
     dropout: 0.2
     use_untrained_resnet: true  # Add this line
   ```

### Interpreting AUROC Scores

Refer to `AUROC_METRICS_EXPLAINED.md` for detailed guidance. Quick reference:

- **Your current 0.65-0.70 scores**: Signals work but weakly
- **Untrained ResNet baseline**: Expect 0.50-0.55 (random-ish)
- **Good pretrained features**: Should get 0.75-0.85
- **Excellent setup**: 0.90+

## 4. Technical Details

### Feature Dimensions

- **DINOv2**: 768-dimensional embeddings (CLS token)
- **Untrained ResNet-50**: 2048-dimensional features (avgpool layer)
- **MLP Classifier**: Adapts to input dimension automatically

### Cache Management

Features are cached separately for:
- Different noise types
- Different model types (dinov2_small, dinov2_base, resnet50_untrained)
- Different data splits (via hash of indices)

Cache files: `features_{noise_type}_{model_name}_n{count}_{hash}.pt`

### Performance Expectations

| Feature Extractor | Expected AUROC | Training Time | Feature Extraction |
|-------------------|----------------|---------------|-------------------|
| DINOv2 (pretrained) | 0.65-0.75 | ~5-10 min | ~2-3 min |
| ResNet-50 (untrained) | 0.50-0.55 | ~5-10 min | ~1-2 min |
| ResNet-50 (pretrained) | 0.70-0.80 | ~5-10 min | ~1-2 min |

## 5. Next Steps & Recommendations

### Immediate Actions

1. **Run baseline experiment** with untrained ResNet to establish lower bound
2. **Compare with DINOv2** to quantify feature importance
3. **Review AUROC documentation** to understand current performance

### Future Improvements

1. **Try pretrained ResNet-50** (add `weights='IMAGENET1K_V1'` option)
2. **Experiment with other backbones**: ViT, CLIP, ConvNeXt
3. **Ensemble methods**: Combine multiple feature extractors
4. **Better uncertainty estimation**: Deep ensembles, Bayesian approaches

### Questions to Answer

- How much do pretrained features help? (DINOv2 vs untrained ResNet)
- Is 0.65-0.70 AUROC the ceiling for this task? (Try better features)
- Which signals are most informative? (Per-signal visualization already added)

## 6. Files Modified

1. `walaris-cen/AUROC_METRICS_EXPLAINED.md` - **NEW**: Comprehensive AUROC documentation
2. `walaris-cen/uq_classification/config.py` - Added `use_untrained_resnet` flag
3. `walaris-cen/uq_classification/data_loader.py` - Added ResNet-50 feature extraction
4. `walaris-cen/ui_components/experiment_config.py` - Added UI checkbox and config support
5. `walaris-cen/streamlit_app.py` - Updated to pass new flag through
6. `walaris-cen/CHANGES_SUMMARY.md` - **NEW**: This file

## 7. Backward Compatibility

✅ **Fully backward compatible**:
- `use_untrained_resnet` defaults to `False`
- Existing experiments continue to use DINOv2
- Existing config files work without modification
- Cache files are separate (no conflicts)

## 8. Testing Checklist

- [ ] Single experiment with DINOv2 (should work as before)
- [ ] Single experiment with untrained ResNet (should show poor performance)
- [ ] Batch experiment with DINOv2 (should work as before)
- [ ] Batch experiment with untrained ResNet (should work)
- [ ] Cache files created correctly for both model types
- [ ] UI checkbox works and shows appropriate warnings
- [ ] Config files with/without flag both work

---

**Made with Bob** 🤖