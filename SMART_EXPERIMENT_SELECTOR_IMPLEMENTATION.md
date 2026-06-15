# Smart Experiment Selector - Implementation Guide

## Overview

The Smart Experiment Selector automatically detects experiment types (1D epistemic, 1D aleatoric, 2D grid, single point) and enables users to create complementary sweeps for complete 2D visualizations.

## Features

### 1. Automatic Experiment Type Detection

```python
from ui_components.smart_experiment_selector import detect_experiment_configuration

config = detect_experiment_configuration(experiments)
# Returns:
# {
#     "type": "1d_aleatoric",  # or "1d_epistemic", "2d_grid", "single_point"
#     "epistemic_values": [300],  # Fixed at 300
#     "aleatoric_values": [0, 25, 50, 75, 100],  # Swept
#     "n_epistemic": 1,
#     "n_aleatoric": 5,
#     "completed_count": 5,
#     "total_count": 5,
#     "needs_complement": True,  # ← Needs epistemic sweep!
#     "complement_type": "epistemic",
#     "complement_values": [50, 100, 200, 300, 500],  # Suggested
# }
```

### 2. Visual Status Indicators

- **📊 1D Epistemic Sweep**: Dataset size varied, noise fixed
- **📊 1D Aleatoric Sweep**: Noise varied, dataset size fixed
- **🎯 2D Grid (Complete)**: Both dimensions swept
- **📍 Single Point**: No sweep, single configuration

### 3. Complementary Sweep Creator

When a 1D sweep is detected, the UI automatically suggests creating the complementary sweep with matching number of points.

**Example**: If you have 5 aleatoric points [0, 25, 50, 75, 100], it suggests 5 epistemic points [50, 100, 200, 300, 500].

## Integration with Streamlit Apps

### Step 1: Import the Component

```python
from ui_components.smart_experiment_selector import render_smart_experiment_selector
```

### Step 2: Add to Your Streamlit App

```python
# In streamlit_app_progressive.py or streamlit_app.py

st.markdown("## 📊 Experiment Visualization")

# Fetch experiments from API
experiments = fetch_experiments_from_api(API_BASE_URL, get_headers)

if experiments:
    # Render smart selector
    selected_batch = render_smart_experiment_selector(
        experiments,
        API_BASE_URL,
        get_headers,
        key_prefix="viz_"
    )
    
    if selected_batch:
        # Visualize the selected batch
        batch_experiments = selected_batch["experiments"]
        batch_config = selected_batch["config"]
        
        if batch_config["type"] in ("1d_epistemic", "1d_aleatoric"):
            # Show 1D sweep plot
            render_production_signal_sweep_grid(
                batch_experiments,
                sweep_type=batch_config["type"].replace("1d_", ""),
            )
        elif batch_config["type"] == "2d_grid":
            # Show 2D heatmap
            render_2d_heatmap(batch_experiments)
        else:
            # Show single point details
            render_single_experiment_details(batch_experiments[0])
```

### Step 3: Connect Complementary Sweep Creation to API

Currently, the sweep creation forms show "API integration pending". To complete:

```python
# In smart_experiment_selector.py, replace TODO sections with:

import requests

def create_complementary_sweep(
    sweep_type: str,  # "epistemic" or "aleatoric"
    sweep_values: List[float],
    fixed_param: Dict[str, float],
    base_config: Dict[str, Any],
    api_base_url: str,
    get_headers_func,
) -> Dict[str, Any]:
    """Create a batch experiment for complementary sweep."""
    
    # Build batch experiment payload
    batch_payload = {
        "name": f"complement_{sweep_type}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}",
        "description": f"Complementary {sweep_type} sweep",
        "base_config": base_config,
        "sweep_definitions": [
            {
                "parameter": EPISTEMIC_PARAM if sweep_type == "epistemic" else ALEATORIC_PARAM,
                "value_type": "int" if sweep_type == "epistemic" else "float",
                "range": {
                    "start": min(sweep_values),
                    "end": max(sweep_values),
                    "step": (max(sweep_values) - min(sweep_values)) / (len(sweep_values) - 1),
                }
            }
        ],
        "auto_start": True,
    }
    
    # POST to batch experiments endpoint
    response = requests.post(
        f"{api_base_url}/api/v1/batch-experiments",
        json=batch_payload,
        headers=get_headers_func(),
        timeout=30
    )
    response.raise_for_status()
    return response.json()
```

## Usage Examples

### Example 1: User Has Aleatoric Sweep, Wants Epistemic

**Current state**:
```
Experiments:
- exp_20260604_120000_noise_0
- exp_20260604_120000_noise_25
- exp_20260604_120000_noise_50
- exp_20260604_120000_noise_75
- exp_20260604_120000_noise_100

Config: under_train_per_class=300 (fixed)
```

**Smart selector shows**:
```
📊 1D Aleatoric Sweep (5/5 completed) ⚠️

Current: 5 aleatoric points (label noise sweep)
Needed: Epistemic sweep (dataset size) with 5 points for balanced 2D grid

Suggested epistemic values: [50, 100, 200, 300, 500]
```

**User clicks "Create Epistemic Sweep"** → 5 new experiments created with:
- `under_train_per_class`: [50, 100, 200, 300, 500]
- `aleatoric_noise_percentage`: 50 (middle value from existing sweep)

**Result**: Now have 10 experiments total (5 aleatoric + 5 epistemic) for 2D visualization

### Example 2: User Has Epistemic Sweep, Wants Aleatoric

**Current state**:
```
Experiments:
- exp_20260604_130000_size_50
- exp_20260604_130000_size_100
- exp_20260604_130000_size_200

Config: aleatoric_noise_percentage=0 (fixed)
```

**Smart selector shows**:
```
📊 1D Epistemic Sweep (3/3 completed) ⚠️

Current: 3 epistemic points (dataset size sweep)
Needed: Aleatoric sweep (label noise) with 3 points for balanced 2D grid

Suggested aleatoric values: [0, 50, 100]
```

**User clicks "Create Aleatoric Sweep"** → 3 new experiments created

**Result**: 6 experiments total (3 epistemic + 3 aleatoric) for 2D visualization

### Example 3: Complete 2D Grid

**Current state**:
```
Experiments: 15 total
- 5 epistemic values × 3 aleatoric values = 15 experiments
```

**Smart selector shows**:
```
🎯 2D Grid (Complete) (15/15 completed) ✅

✅ This experiment configuration is complete for 2D visualization.
```

**No complementary sweep needed** - can directly visualize 2D heatmap

## Visualization Flow

```
User selects batch
       ↓
Detect experiment type
       ↓
   ┌───────────────────────────────────┐
   │                                   │
   ↓                                   ↓
1D Sweep                          2D Grid
   │                                   │
   ↓                                   ↓
Show 1D plot                    Show 2D heatmap
   │                                   │
   ↓                                   
Offer complementary sweep              
   │                                   
   ↓                                   
User creates complement                
   │                                   
   ↓                                   
Wait for completion                    
   │                                   
   ↓                                   
Refresh → Now 2D Grid ──────────────────┘
```

## API Endpoints Needed

### 1. Batch Experiment Creation (Already Exists)

```
POST /api/v1/batch-experiments
```

Payload:
```json
{
  "name": "complement_epistemic_20260604_120000",
  "description": "Complementary epistemic sweep",
  "base_config": { ... },
  "sweep_definitions": [
    {
      "parameter": "under_train_per_class",
      "value_type": "int",
      "range": {
        "start": 50,
        "end": 500,
        "step": 112.5
      }
    }
  ],
  "auto_start": true
}
```

### 2. Experiment Grouping (Optional Enhancement)

```
GET /api/v1/experiments/groups
```

Returns experiments grouped by batch timestamp for easier selection.

## Testing Plan

### Test 1: Aleatoric → Epistemic Complement

1. Create aleatoric sweep: [0, 25, 50, 75, 100]
2. Wait for completion
3. Open smart selector
4. Verify it detects "1D Aleatoric" with 5 points
5. Click "Create Epistemic Sweep"
6. Verify 5 epistemic experiments are created
7. Wait for completion
8. Refresh selector
9. Verify it now shows "2D Grid (Complete)"

### Test 2: Epistemic → Aleatoric Complement

1. Create epistemic sweep: [50, 100, 200]
2. Wait for completion
3. Open smart selector
4. Verify it detects "1D Epistemic" with 3 points
5. Click "Create Aleatoric Sweep"
6. Verify 3 aleatoric experiments are created
7. Wait for completion
8. Refresh selector
9. Verify it now shows "2D Grid (Complete)"

### Test 3: Single Point → Both Sweeps

1. Create single experiment
2. Open smart selector
3. Verify it shows "Single Point"
4. Create epistemic sweep first
5. After completion, create aleatoric sweep
6. Verify final state is "2D Grid (Complete)"

## Next Steps

1. ✅ Component created: `ui_components/smart_experiment_selector.py`
2. ⏳ Integrate into `streamlit_app_progressive.py`
3. ⏳ Connect sweep creation to batch experiments API
4. ⏳ Add 2D heatmap visualization for complete grids
5. ⏳ Test full workflow end-to-end
6. ⏳ Add progress tracking for running complementary sweeps
7. ⏳ Document in main README

## Files Modified/Created

- ✅ `ui_components/smart_experiment_selector.py` - Main component
- ⏳ `ui_components/__init__.py` - Export new functions
- ⏳ `streamlit_app_progressive.py` - Integration
- ⏳ `streamlit_app.py` - Integration
- ✅ `EPISTEMIC_UNCERTAINTY_EXPLAINED.md` - Documentation
- ✅ `SMART_EXPERIMENT_SELECTOR_IMPLEMENTATION.md` - This file