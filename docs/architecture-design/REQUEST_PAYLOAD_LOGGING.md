# Request Payload Logging Added to Streamlit Frontend

## Summary
Added comprehensive request payload logging to the Streamlit progressive UI to debug why DINOv2 configuration is being sent when users select ResNet.

## Changes Made

### 1. Step 5 Review Section (Lines ~1438-1463)
**Location:** `streamlit_app_progressive.py` - Step 5: Review section

**Added:**
- Full workflow state viewer (expandable JSON)
- Current model architecture display
- Visual indicators for ResNet vs DINOv2 selection
- Expected configuration values based on selection

**Purpose:** Shows the workflow state BEFORE configs are generated, helping identify if the issue is in the UI form building.

### 2. Launch Function Logging (Lines ~424-470)
**Location:** `streamlit_app_progressive.py` - `_launch_workflow_experiments()` function

**Added:**
- Total experiments counter
- Per-experiment expandable sections showing:
  - Full request payload as JSON
  - Key configuration values in a readable format:
    - Architecture
    - DINOv2 model
    - Hidden dimension
    - Dropout
    - Under-train per class
    - Regular train per class
    - Aleatoric noise percentage
    - Noise type
  - Original workflow model_architecture value

**Purpose:** Shows the EXACT payload being sent to the API for each experiment, making it easy to see if DINOv2 is incorrectly set.

## How to Use

### For Users:
1. Navigate through the progressive UI steps
2. At **Step 5: Review**, you'll see:
   - A debug section showing your selected model architecture
   - Expected configuration based on your selection
   - Full workflow state (expandable)

3. When you launch experiments, you'll see:
   - A "DEBUG: Request Payload Logging" section
   - Expandable cards for each experiment showing the exact API payload
   - The first experiment is expanded by default

### What to Look For:

**If ResNet is selected:**
- `workflow['training_config']['model_architecture']` should be `"resnet18"` or `"resnet50"`
- In the payload, `config.model.architecture` should be `"resnet18_mcdropout"`
- `config.model.dinov2_model` will show `"small"` but should be ignored (this is the bug!)

**If DINOv2 is selected:**
- `workflow['training_config']['model_architecture']` should be `"dinov2-small"` or `"dinov2-base"`
- In the payload, `config.model.architecture` should be `"dinov2_mlp"`
- `config.model.dinov2_model` should be `"small"` or `"base"`

## Known Issue Identified

In `_workflow_to_experiment_config()` (lines 358-365), there's a bug:

```python
# Determine architecture from model selection
model_arch = training.get("model_architecture", "resnet18")
if "resnet" in model_arch.lower():
    architecture = "resnet18_mcdropout"
    dinov2_model = "small"  # ❌ BUG: Always set to "small" even for ResNet!
else:
    architecture = "dinov2_mlp"
    dinov2_model = _normalize_dinov2_model(model_arch)
```

**The Issue:** Even though `dinov2_model` is not used when `architecture="resnet18_mcdropout"`, it's still being set to `"small"` and sent in the payload. This might confuse the backend or cause issues if the backend doesn't properly ignore it.

## Next Steps

1. **Verify the issue:** Run the app and create an experiment with ResNet selected
2. **Check the payload:** Look at the debug output to confirm `dinov2_model="small"` is being sent
3. **Fix if needed:** Either:
   - Set `dinov2_model = None` for ResNet (requires backend to handle None)
   - Set `dinov2_model = ""` for ResNet
   - Update backend to completely ignore `dinov2_model` when architecture is ResNet

## Testing

To test the logging:
```bash
cd uqlab-streamlit
streamlit run streamlit_app_progressive.py
```

Then:
1. Go through Steps 1-4
2. At Step 2, select "resnet18" or "resnet50"
3. At Step 5, check the debug output
4. Launch an experiment and inspect the payload logging