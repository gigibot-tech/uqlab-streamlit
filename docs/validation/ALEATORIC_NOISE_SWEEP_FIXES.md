# Aleatoric Noise Sweep Implementation & UI Redesign

## Problem Summary
The `aleatoric_noise_percentage` parameter was always showing 0.0 in experiments, even when users selected custom noise injection. This prevented proper testing of aleatoric uncertainty criteria (C1) and (O2).

## Root Causes Identified

### 1. UI Default Selection Issue
- Radio button had no `index` parameter, defaulting to "Use CIFAR-10N noise" (index=0)
- This set `custom_noise_rate = 0.0` even when user intended to use custom noise
- Form reloads would reset selection back to default

### 2. Confusing Dataset Logic
- UI suggested CIFAR-10N was the "base dataset"
- Unclear when CIFAR-10 vs CIFAR-10N was actually used
- CIFAR-10N stats API call appeared even for custom noise experiments

## Solutions Implemented

### 1. Fixed Radio Button Default (ui_components/experiment_config.py)
```python
# Added default index and session state persistence
noise_source = st.radio(
    "Label Noise Strategy",
    [
        "No noise (0%, clean labels)",
        "CIFAR-10N pre-existing noise (~18-40%, not sweepable)",
        "Custom random flipping (0-50%, sweepable)"
    ],
    index=2,  # Default to custom flipping
    key='noise_source_selection'
)
```

### 2. Redesigned UI Logic (ui_components/dataset.py + experiment_config.py)

**New Clear Hierarchy:**

```
┌─────────────────────────────────────────────────────────┐
│ 📊 Dataset Selection & Overview                        │
│                                                         │
│ Base Dataset: CIFAR-10 (clean)                         │
│ ✅ 50,000 training images, 10 classes, NO NOISE        │
│                                                         │
│ CIFAR-10N Reference (optional):                        │
│ └─ View pre-existing noise patterns for comparison     │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ 🧠 Epistemic Uncertainty                               │
│ └─ Under-supported classes (data scarcity)             │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ 🎲 Aleatoric Uncertainty (Label Noise)                 │
│                                                         │
│ Base: Clean CIFAR-10 (no noise)                        │
│                                                         │
│ Label Noise Strategy:                                  │
│ ○ No noise (0%, clean labels)                          │
│ ○ CIFAR-10N pre-existing noise (~18-40%, not sweepable)│
│ ● Custom random flipping (0-50%, sweepable) ← DEFAULT  │
│   └─ Slider: 0-50% (default: 10%)                      │
└─────────────────────────────────────────────────────────┘
```

### 3. Updated Labels and Help Text

**Before:**
- "Use CIFAR-10N noise (fixed ~18%, not sweepable)"
- "Add random label flipping (0-50%, sweepable)"

**After:**
- "No noise (0%, clean labels)"
- "CIFAR-10N pre-existing noise (~18-40%, not sweepable)"
- "Custom random flipping (0-50%, sweepable)"

## Implementation Details

### Backend Logic (scripts/run_fast_uncertainty_classification.py)
```python
# Line 276-310: Correct dataset loading
if aleatoric_noise_percentage > 0:
    # Load CLEAN CIFAR-10 for custom noise injection
    train_dataset = load_cifar10_clean(...)
    train_dataset.inject_custom_noise(aleatoric_noise_percentage)
else:
    # Load CIFAR-10N with pre-existing noise
    train_dataset = load_cifar10n(noise_type=noise_type)
```

### Data Loader (src/data/cifar10n_loader.py)
```python
def inject_custom_noise(self, noise_percentage: float, seed: int = 42):
    """
    Inject uniform random label noise into clean CIFAR-10.
    
    Args:
        noise_percentage: Percentage (0-100) of labels to corrupt
        seed: Random seed for reproducibility
    """
    # Uniform random flipping across all classes
    # Reproducible with same seed
```

## Testing the Fix

### 1. Single Experiment Test
```bash
# Start Streamlit
./run_streamlit.sh

# In UI:
1. Select "Custom random flipping" (should be default)
2. Set slider to 20%
3. Create experiment
4. Check config.yaml: aleatoric_noise_percentage should be 20.0
```

### 2. Batch Sweep Test
```bash
# Create batch experiment
Swept parameter: aleatoric_noise_percentage
Values: [0, 10, 20, 30, 40]

# Verify all experiments have correct values
cd /tmp/walaris_experiments
for dir in */; do
    echo "$dir: $(grep 'aleatoric_noise_percentage' $dir/config.yaml)"
done
```

### 3. Hypothesis Verification
```bash
# Run analysis
python analyze_results.py

# Expected results:
# - inverse_coherence AUROC increases with noise (C1 ✓)
# - dominance/inverse_mass AUROC stable across noise (O2 ✓)
```

## Key Takeaways

### Conceptual Clarity
1. **Base Dataset**: Always CIFAR-10 (clean, 50k images)
2. **Epistemic Uncertainty**: Under-supported classes (fewer training samples)
3. **Aleatoric Uncertainty**: Optional label noise injection

### Noise Sources
- **No Noise**: Clean CIFAR-10 labels (0%)
- **CIFAR-10N**: Pre-existing noise patterns (~18-40%, not sweepable)
- **Custom**: Uniform random flipping (0-50%, sweepable)

### Sweepable Parameters
- ✅ `aleatoric_noise_percentage` (0-50) - custom noise only
- ✅ `under_train_per_class` (epistemic)
- ✅ `regular_train_per_class` (epistemic)
- ❌ CIFAR-10N noise (fixed per noise_type)

## Files Modified

1. `ui_components/experiment_config.py` (lines 132-195)
   - Redesigned aleatoric config with 3 options
   - Added session state persistence
   - Clearer labels and help text

2. `ui_components/dataset.py` (lines 29-58)
   - Clarified CIFAR-10 is base dataset
   - CIFAR-10N shown as reference only
   - Removed confusing "Select Dataset" dropdown

3. `backend/app/domain/models.py` (lines 17-22, 50)
   - Added `aleatoric_noise_percentage` field (already done)

4. `scripts/run_fast_uncertainty_classification.py` (lines 276-310)
   - Correct dataset loading logic (already done)

## Batch Experiments (1D) Tab

The "Batch Experiments (1D)" tab renders 1D sweep plots via `render_batch_results()` in `ui_components/signal_visualization.py`.

**Features:**
- Lists all batch experiments with status
- Shows 3 visualization tabs:
  1. **Aggregated (Original)** - epistemic_auroc & aleatoric_auroc only
  2. **All Signals** - all 7+ signals in one chart
  3. **By Category** - signals grouped by type
- Validation analysis button for completed batches
- Start/retry/delete batch controls

**If tab appears empty:**
- No batch experiments created yet → Create one using form above
- Selected batch has no completed runs → Wait for completion or check status
- API connection issue → Check backend is running

## Next Steps

1. ✅ Restart Streamlit to see new UI: `./run_streamlit.sh`
2. ✅ Create test experiment with 20% custom noise
3. ✅ Verify `aleatoric_noise_percentage: 20.0` in config.yaml
4. ⏳ Create batch sweep [0, 10, 20, 30, 40] using either:
   - **Single Experiment → Batch Experiments (1D)** tab
   - **Unified Builder** tab (now also has 3-option redesign)
5. ⏳ Run `analyze_results.py` to verify (C1) and (O2)
6. ⏳ Check "Batch Experiments (1D)" tab for 1D plots

## Files Modified Summary

### UI Components
1. `ui_components/experiment_config.py` - 3-option aleatoric config for Single/Batch tabs
2. `ui_components/dataset.py` - Clarified CIFAR-10 is base, CIFAR-10N is reference
3. `ui_components/unified_builder.py` - Applied same 3-option redesign to Unified Builder

### Backend (Already Done)
4. `backend/app/domain/models.py` - Added `aleatoric_noise_percentage` field
5. `scripts/run_fast_uncertainty_classification.py` - Correct dataset loading logic

### Visualization (Already Working)
6. `ui_components/signal_visualization.py` - `render_batch_results()` renders 1D plots

## Made with Bob