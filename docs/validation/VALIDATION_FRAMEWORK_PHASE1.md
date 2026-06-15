# Experiment Validation Framework - Phase 1 Complete ✅

## Overview

Phase 1 implements experiment type validation tags in the Streamlit UI, allowing users to mark experiments as testing specific uncertainty types according to the theoretical framework for uncertainty disentanglement.

## Theoretical Framework

Based on the paper's methodology:

### Experiment Types

1. **Epistemic Sweep**: Varies training data size to control model uncertainty (Ue)
   - Parameter: `under_train_per_class` or `regular_train_per_class`
   - Expected: C2 (ue ∼∝ Ue) and O1 (ua ⊥ Ue)

2. **Aleatoric Sweep**: Varies label noise to control data uncertainty (Ua)
   - Parameter: `aleatoric_noise_percentage`
   - Expected: C1 (ua ∼∝ Ua) and O2 (ue ⊥ Ua)

3. **2D Grid Sweep**: Tests both simultaneously (epistemic × aleatoric)
   - Parameters: Both `under_train_per_class` and `aleatoric_noise_percentage`
   - Expected: All four conditions (C1, C2, O1, O2)

### Validation Criteria

- **Consistency**: 
  - C1: Aleatoric signal (ua) should correlate with noise level (ρ > 0.7)
  - C2: Epistemic signal (ue) should correlate with training size (ρ > 0.7)

- **Orthogonality**:
  - O1: Aleatoric signal (ua) should be independent of training size (ρ < 0.3)
  - O2: Epistemic signal (ue) should be independent of noise level (ρ < 0.3)

## Implementation

### New Files

1. **`ui_components/experiment_validation.py`** (244 lines)
   - `render_experiment_type_validation()`: Checkbox UI for marking experiment types
   - `render_validation_summary()`: Display expected outcomes
   - `get_validation_badge()`: Badge strings for experiment types
   - `validate_sweep_configuration()`: Configuration validation

### Modified Files

1. **`ui_components/__init__.py`**
   - Exported validation functions

2. **`streamlit_app.py`**
   - Added validation imports
   - **Single Experiment Tab**: Manual validation checkboxes
   - **1D Batch Tab**: Auto-detect validation based on swept parameter
   - **2D Grid Tab**: Auto-detect as epistemic × aleatoric
   - Validation metadata added to all experiment configs

### Validation Metadata Structure

```python
validation_metadata = {
    'validation_enabled': bool,
    'is_epistemic_sweep': bool,
    'is_aleatoric_sweep': bool,
    'epistemic_parameter': str or None,
    'aleatoric_parameter': str or None
}
```

This metadata is stored in the experiment config and will be used by Phase 2 for correlation analysis.

## User Experience

### Single Experiments

Users can manually mark experiments:
```
🔬 Experiment Type Validation
├─ 📊 Epistemic Sweep
│  └─ Checkbox: "Mark as Epistemic Sweep"
│     └─ Select swept parameter
└─ 🎲 Aleatoric Sweep
   └─ Checkbox: "Mark as Aleatoric Sweep"
      └─ Select swept parameter
```

### 1D Batch Experiments

Auto-detection based on swept parameter:
- Sweeping `under_train_per_class` → ✅ Epistemic Sweep
- Sweeping `aleatoric_noise_percentage` → ✅ Aleatoric Sweep
- Other parameters → ℹ️ Not a standard validation parameter

### 2D Grid Experiments

Always auto-detected as full framework validation:
```
✅ Auto-detected: 2D Grid Sweep (Epistemic × Aleatoric)

This experiment will validate the full uncertainty disentanglement framework:
- C1: Aleatoric signal (ua) correlates with noise level
- C2: Epistemic signal (ue) correlates with training size
- O1: Aleatoric signal (ua) independent of training size
- O2: Epistemic signal (ue) independent of noise level
```

## Example Usage

### Creating a Validated Epistemic Sweep

1. Go to "Batch Experiments (1D)" tab
2. Select swept parameter: `under_train_per_class`
3. Set sweep range: 50, 100, 200
4. System auto-detects: ✅ Epistemic Sweep
5. Submit → All experiments tagged with validation metadata

### Creating a Validated 2D Grid

1. Go to "Batch Experiments (2D Grid)" tab
2. Configure epistemic values: [1, 101, 301]
3. Configure aleatoric values: [0, 25, 50]
4. System auto-detects: ✅ 2D Grid Sweep
5. Submit → 9 experiments created, all tagged for full validation

## Data Storage

Validation metadata is stored in two places:

1. **Experiment Config** (YAML file):
```yaml
validation_metadata:
  validation_enabled: true
  is_epistemic_sweep: true
  is_aleatoric_sweep: false
  epistemic_parameter: under_train_per_class
  aleatoric_parameter: null
```

2. **Database** (via config field):
   - Stored as part of the experiment configuration
   - Accessible for filtering and analysis

## Next Steps

### Phase 2: Correlation Analysis (Pending)

Implement correlation analysis to validate experiments:

1. **Load Results**: Extract uncertainty signals from completed experiments
2. **Calculate Correlations**: 
   - ρ(ue, Ue) for epistemic sweeps
   - ρ(ua, Ua) for aleatoric sweeps
   - All four correlations for 2D grids
3. **Compute UDE**: Uncertainty Disentanglement Error metric
4. **Visualize**: Correlation plots and scatter matrices

### Phase 3: Compliance Dashboard (Pending)

Build dashboard to display validation results:

1. **Per-Experiment View**: Show C1/C2/O1/O2 compliance
2. **Aggregate View**: Compare experiments
3. **Visual Indicators**: ✅ ⚠️ ❌ for each condition
4. **Recommendations**: Suggest improvements

## Technical Notes

### Backward Compatibility

- Validation metadata is optional
- Existing experiments without metadata work normally
- New experiments can opt-in to validation

### Performance

- No performance impact on experiment execution
- Validation is metadata-only in Phase 1
- Actual validation computation happens in Phase 2

### Testing

To test the validation UI:

1. Start Streamlit: `streamlit run streamlit_app.py`
2. Create a single experiment with validation checkboxes
3. Create a 1D batch with epistemic sweep
4. Create a 2D grid sweep
5. Check that validation metadata appears in experiment configs

## Summary

✅ **Phase 1 Complete**: Experiment type validation tags implemented
- Manual validation for single experiments
- Auto-detection for batch experiments
- Validation metadata stored in configs
- Ready for Phase 2 correlation analysis

📊 **Impact**: Users can now mark experiments for theoretical framework validation, enabling systematic evaluation of uncertainty disentanglement quality.

---

**Made with Bob** 🤖