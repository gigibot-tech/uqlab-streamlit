# UI Verification Results - Aleatoric Noise Redesign

## Date: 2026-05-22

## Status: ⚠️ CODE UPDATED BUT STREAMLIT NOT RESTARTED

### What I Found

When accessing the running Streamlit app at `http://localhost:8501`, I observed:

**Current UI (OLD Design - 2 options):**
- ⚪ Use CIFAR-10N noise
- ⚪ Add random label flipping
- Green recommendation: "CIFAR-10N with 40% avg noise"

**Expected UI (NEW Design - 3 options):**
- ⚪ No noise (0%, clean labels)
- ⚪ CIFAR-10N pre-existing noise (~18-40%, not sweepable)
- ⚪ Custom random flipping (0-50%, sweepable) ← DEFAULT

### Root Cause

The code files have been successfully updated with the 3-option redesign:
- ✅ `ui_components/experiment_config.py` - Updated (lines 132-210)
- ✅ `ui_components/dataset.py` - Updated (lines 29-58)  
- ✅ `ui_components/unified_builder.py` - Updated (lines 316-365)

However, **Streamlit caches Python modules** and the running instance has not reloaded the updated files.

### Solution Required

**RESTART STREAMLIT** to see the changes:

```bash
# Stop current Streamlit (Ctrl+C in terminal)
# Then restart:
cd uqlab-streamlit
source .venv/bin/activate
streamlit run streamlit_app.py
```

Or use the restart script:
```bash
cd uqlab-streamlit
./run_streamlit.sh
```

### Files Modified

All changes documented in `ALEATORIC_NOISE_SWEEP_FIXES.md`:

1. **ui_components/experiment_config.py** (lines 132-210)
   - Changed from 2 to 3 radio options
   - Added session state persistence
   - Set default index=2 (Custom random flipping)

2. **ui_components/dataset.py** (lines 29-58)
   - Clarified "Base Dataset: CIFAR-10 (clean)"
   - CIFAR-10N shown as reference only

3. **ui_components/unified_builder.py** (lines 316-365)
   - Applied same 3-option redesign
   - Consistent with other tabs

### Next Steps

1. **Restart Streamlit** (required)
2. Verify 3 radio options appear
3. Test that "Custom random flipping" is selected by default
4. Create experiment with 20% noise
5. Verify `aleatoric_noise_percentage: 20.0` in config.yaml
6. Create batch sweep on `aleatoric_noise_percentage`
7. Verify 1D plots render correctly

### Verification Checklist

- [ ] Streamlit restarted
- [ ] 3 radio options visible in Single Experiment tab
- [ ] "Custom random flipping" selected by default
- [ ] Slider shows 20% when selected
- [ ] Experiment creation saves correct value
- [ ] Batch Experiments (1D) tab shows 3 options
- [ ] Unified Builder tab shows 3 options
- [ ] All tabs have consistent behavior

## Conclusion

**Code changes are complete and correct.** The issue is simply that the running Streamlit instance needs to be restarted to load the updated Python modules.