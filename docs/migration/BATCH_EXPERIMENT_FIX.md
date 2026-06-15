# How to Fix Your Batch Experiment

## Problem Identified

Your batch experiment is failing because the **base configuration** has invalid parameters:

```yaml
# ❌ CURRENT (WRONG)
data:
  eval_per_group: 100              # Too small!
  regular_train_per_class: null    # Missing!
  under_supported_classes: 0,1     # Wrong classes!
```

This causes:
- Only 2 under-supported classes (0,1) instead of (3,5)
- 8 "regular" classes but `regular_train_per_class` is null
- `eval_per_group=100` is too small
- Result: Clean and aleatoric pools are EMPTY

## Solution

Create a NEW batch with CORRECT base configuration:

```yaml
# ✅ CORRECT
data:
  eval_per_group: 600
  regular_train_per_class: 300
  under_supported_classes: "3,5"
  under_train_per_class: null  # This will be swept
```

## Step-by-Step Fix

### 1. In Streamlit UI

Go to "Batch Experiments" tab and create new batch with:

**Base Configuration:**
- Noise Type: `worse_label`
- Under Supported Classes: `3,5` ← **IMPORTANT!**
- Under Train Per Class: Leave empty (will be swept)
- Regular Train Per Class: `300` ← **IMPORTANT!**
- Eval Per Group: `600` ← **IMPORTANT!**

**Sweep Definition:**
- Parameter: `under_train_per_class`
- Start: `5`
- End: `50`
- Step: `5`

This will create 10 runs: [5, 10, 15, 20, 25, 30, 35, 40, 45, 50]

### 2. Via API (if using direct API calls)

```bash
curl -X POST "http://localhost:8000/api/v1/batch-experiments" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Under-Training Sweep (Fixed)",
    "description": "Sweep under_train_per_class with correct base config",
    "base_config": {
      "noise_type": "worse_label",
      "under_supported_classes": "3,5",
      "under_train_per_class": null,
      "regular_train_per_class": 300,
      "eval_per_group": 600,
      "dinov2_model": "small",
      "hidden_dim": 256,
      "dropout": 0.2,
      "epochs": 12,
      "learning_rate": 0.001,
      "weight_decay": 0.0001,
      "train_batch_size": 256,
      "mc_passes": 20,
      "attribution_method": "dualxda"
    },
    "sweep_definition": {
      "parameter": "under_train_per_class",
      "value_type": "int",
      "range": {
        "start": 5,
        "end": 50,
        "step": 5
      }
    }
  }'
```

## Why This Works

With correct parameters:

**Under-supported classes (3, 5):**
- 2 classes with reduced training samples
- Need: `under_train_per_class` (5-50) + `eval_per_group` (600) = 605-650 samples
- Available: ~3000 clean samples per class
- ✅ **Plenty of room!**

**Regular classes (0, 1, 2, 4, 6, 7, 8, 9):**
- 8 classes with normal training samples
- Training uses: 300 samples per class
- Eval needs: 600 total / 8 classes = 75 per class
- After training: ~2700 samples remain per class
- ✅ **More than enough!**

## Validation Will Pass

The new batch will pass validation because:
- Epistemic pool: 50 + 600 = 650 ≤ 3000 ✅
- Aleatoric pool: 75 ≤ 1880 remaining noisy ✅
- Clean pool: 75 ≤ 2820 remaining clean ✅

## Expected Result

All 10 runs should complete successfully with:
- Training on intentionally imbalanced data
- Evaluation on three distinct uncertainty groups
- AUROC curves showing performance vs `under_train_per_class`

---

**TL;DR**: Delete the current batch and create a new one with:
- `under_supported_classes: "3,5"` (not "0,1")
- `regular_train_per_class: 300` (not null)
- `eval_per_group: 600` (not 100)