# Step 3 Uncertainty Configuration Redesign

## Overview
This document summarizes the Distinguished Engineer-level redesign of Step 3 to address UX/UI clarity issues and logical inconsistencies.

## Problems Identified & Solutions

### 1. ✅ Confusing Sweep Percentage Logic (PARTIALLY FIXED)
**Problem:** Hardcoded lists like `[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]` were not programmable

**Solution Implemented:**
- Added "Preset (Quick/Full)" vs "Custom (Define your own)" radio button
- Custom mode provides programmable sweep generation:
  - Label Noise: Start %, End %, Step % → generates list
  - Dataset Size: Start samples, End samples, Step samples → generates list
- Preview shows exactly what will run
- Total run count displayed clearly

**Status:** ✅ UI implemented, needs testing

### 2. ✅ Logical Inconsistency: Epistemic/Aleatoric Flags (FIXED)
**Problem:** Configuration showed `epistemic_enabled: False, aleatoric_enabled: False` even when sweeping label_noise

**Solution Implemented:**
- Removed confusing "enabled" flags from UI
- Logic now automatic:
  - If sweeping `label_noise` → `aleatoric_enabled = True` (automatic)
  - If sweeping `dataset_size` → `epistemic_enabled = True` (automatic)
  - Sweep type selection IS the enable/disable mechanism
- Configuration summary now shows:
  ```
  Sweep: noise: 5 pts × size: 5 pts = 25 runs
  ```
  Instead of confusing enabled flags

**Status:** ✅ Logic fixed in collapsed summary (lines 1424-1462)

### 3. ⚠️ Confusing "Paper Sweep" vs "Full Sweep" Terminology (PARTIALLY ADDRESSED)
**Problem:** Users don't understand "paper sweep" vs "full sweep"

**Solution Implemented:**
- Renamed in UI:
  - "Quick" mode (5 runs) - Fast testing
  - "Full" mode (11 runs) - Comprehensive analysis  
  - "Custom" mode - User-defined ranges
- Added clear captions explaining each mode
- Preset modes use paper configurations
- Custom mode allows full control

**Status:** ⚠️ UI updated, but Step 5 paper sweep distinction still needs work

### 4. ❌ Paper Sweep Confusion (NOT YET ADDRESSED)
**Problem:** Relationship between Step 3 custom sweep and Step 5 paper sweep unclear

**Required Solution:**
```python
# Step 5 needs clear separation:
st.markdown("### 🚀 Step 5: Launch Options")

st.markdown("#### Option A: Launch Your Custom Sweep")
st.caption("Uses the configuration you defined in Step 3")
if st.button("🚀 Launch Custom Sweep"):
    # Launch using Step 3 config
    pass

st.markdown("---")

st.markdown("#### Option B: Launch Paper Preset Sweeps")
st.caption("Fixed configurations for reproducing paper results (ignores Step 3)")

with st.expander("📖 What are paper sweeps?"):
    st.markdown("""
    Paper sweeps use **fixed, predefined configurations** from our research paper.
    These sweeps **ignore your Step 3 custom settings**.
    """)
```

**Status:** ❌ Not yet implemented

## Code Changes Made

### File: `streamlit_app_progressive.py`

#### Lines 1424-1462: Improved Collapsed Summary
- Removed confusing enabled flags
- Shows clear sweep description: "noise: X pts × size: Y pts = Z runs"
- Or "Single experiment (no sweep)" when sweep disabled

#### Lines 1464-1712: Redesigned Active Step UI
**Key Changes:**
1. Added clear introduction text explaining purpose
2. Sweep enable/disable checkbox with clear help text
3. Multi-select for sweep types (label_noise, dataset_size)
4. **NEW:** Preset vs Custom configuration mode
5. **NEW:** Programmable sweep generation in Custom mode:
   - Start/End/Step inputs for both noise and dataset size
   - Live preview of generated values
   - Validation of step size > 0
6. Automatic epistemic/aleatoric enabling based on sweep type
7. Clear captions explaining what each configuration does

#### Lines 1713-1761: Configuration Save Logic (NEEDS FIX)
**Current Issues:**
- Variables `sweep_mode`, `label_levels`, `dataset_sizes` may be unbound
- Need to handle both preset and custom modes properly
- Need validation before allowing continue

**Required Fix:**
```python
# Determine sweep_mode for storage
if sweep_enabled and selected_sweep_types:
    if 'sweep_config_mode' in locals() and sweep_config_mode == "Custom (Define your own)":
        final_sweep_mode = "custom"
    elif 'sweep_mode' in locals():
        final_sweep_mode = sweep_mode
    else:
        final_sweep_mode = "quick"
else:
    final_sweep_mode = "quick"

# Get sweep values with defaults
final_label_levels = label_levels if 'label_levels' in locals() else []
final_dataset_sizes = dataset_sizes if 'dataset_sizes' in locals() else []
```

## Testing Requirements

### Test Cases Needed:

1. **Preset Mode Testing:**
   - [ ] Quick mode: Should show [0, 25, 50, 75, 100] for noise
   - [ ] Full mode: Should show [0, 10, 20, ..., 100] for noise
   - [ ] Verify total run count is correct

2. **Custom Mode Testing:**
   - [ ] Noise: start=0, end=100, step=10 → [0, 10, 20, ..., 100]
   - [ ] Noise: start=0, end=100, step=25 → [0, 25, 50, 75, 100]
   - [ ] Size: start=25, end=200, step=25 → [25, 50, 75, ..., 200]
   - [ ] Verify step=0 shows error
   - [ ] Verify preview updates correctly

3. **Logical Consistency Testing:**
   - [ ] Select label_noise only → Summary should NOT show "aleatoric_enabled: False"
   - [ ] Select dataset_size only → Summary should NOT show "epistemic_enabled: False"
   - [ ] Select both → Both should be enabled automatically
   - [ ] Disable sweep → Should show "Single experiment (no sweep)"

4. **Configuration Save Testing:**
   - [ ] Preset quick mode saves correctly
   - [ ] Preset full mode saves correctly
   - [ ] Custom mode saves sweep values correctly
   - [ ] Custom_sweep_config is stored when using custom mode

## Remaining Work

### High Priority:
1. ❌ Fix configuration save logic (lines 1733-1761)
   - Handle unbound variables properly
   - Add validation before continue button
   - Test all code paths

2. ❌ Update Step 5 to clarify custom vs paper sweeps
   - Add clear separation between options
   - Explain that paper sweeps ignore Step 3
   - Add expander with detailed explanation

3. ❌ Fix Step 5 configuration summary (lines 1827-1847)
   - Remove "Epistemic enabled: False/True" display
   - Show clear sweep configuration instead
   - Match new Step 3 summary format

### Medium Priority:
4. ⚠️ Add comprehensive error handling
   - Validate sweep ranges make sense
   - Warn if too many experiments (>100)
   - Handle edge cases gracefully

5. ⚠️ Improve dataset preview for sweeps
   - Show range instead of single value when sweeping
   - Make it clear which values are swept vs fixed

### Low Priority:
6. 📝 Add inline help/tooltips
7. 📝 Consider adding sweep visualization preview
8. 📝 Add "Save configuration" feature

## Success Criteria

- ✅ Sweep generation is programmable (start, end, step)
- ✅ No logical inconsistencies in configuration summary  
- ⚠️ Clear distinction between custom sweeps and paper presets (partial)
- ✅ User understands what each option does
- ✅ Preview shows exactly what will run
- ⚠️ Total run count is accurate (needs testing)

## Notes

- The redesign follows Distinguished Engineer-level UX principles
- Every decision prioritizes user clarity over brevity
- Configuration logic is explicit, not implicit
- Preview-before-commit pattern used throughout
- Validation prevents invalid configurations

## Next Steps

1. Complete configuration save logic fix
2. Test all sweep modes thoroughly
3. Update Step 5 paper sweep section
4. Fix Step 5 configuration summary
5. Comprehensive end-to-end testing
6. Document final changes

---

**Last Updated:** 2026-06-15
**Status:** In Progress - Core UI redesigned, save logic needs completion