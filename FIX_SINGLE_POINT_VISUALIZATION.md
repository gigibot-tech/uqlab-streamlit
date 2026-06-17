# Fix: Single Point Visualization Issue

## Problem

You're seeing plots with only ONE data point (at noise=0) like this:

```
Inverse Coherence    Dominance    Inverse Mass
     ●                  ●              ●
     |                  |              |
     0────────────100   0────────100   0────────100
```

This looks broken because **you created a single experiment, not a sweep**.

## Root Cause

**Single experiment** = 1 configuration = 1 data point
**Sweep** = Multiple configurations = Multiple data points (proper line plot)

The visualization code expects a sweep (≥2 points) but got a single experiment.

## Solution: Create a Batch Sweep

### Option 1: Use Streamlit "Batch Experiments" Tab

1. Open Streamlit app
2. Click **"Batch Experiments"** tab (not "Single Experiment")
3. Configure sweep:
   ```
   Swept Parameter: aleatoric_noise_percentage
   Start: 0
   End: 100
   Step: 25
   ```
   This creates: [0, 25, 50, 75, 100] = 5 experiments

4. Set base configuration (same as before):
   - Under-train: 50
   - Regular-train: 300
   - Epochs: 2 (quick) or 12 (full)
   - MC passes: 10 or 20

5. Click "🚀 Create Batch Experiment"

6. Wait for all 5 to complete

7. **Now the plot will show 5 points connected by lines** ✅

### Option 2: Use Progressive App Default Sweep

The `streamlit_app_progressive.py` has sweep enabled by default:

```python
"uncertainty_config": {
    "sweep_enabled": True,
    "aleatoric_sweep_values": [0, 25, 50, 75, 100],  # 5 points
}
```

Just click "Launch fast sweep (5 runs)" instead of single experiment.

### Option 3: Run Script with Sweep

```bash
cd uqlab-streamlit
source .venv/bin/activate

# Create 5 experiments with different noise levels
for noise in 0 25 50 75 100; do
  python scripts/run_fast_uncertainty_classification.py \
    --noise-type worse_label \
    --aleatoric-noise-percentage $noise \
    --under-train-per-class 50 \
    --regular-train-per-class 300 \
    --epochs 2 \
    --mc-passes 10 \
    --experiment-name "sweep_noise_${noise}"
done
```

## What You Should See After Creating Sweep

### Before (Single Point - Broken):
```
Inverse Coherence
2.5 |
2.0 |
1.5 |     ●  (only one point at noise=0)
1.0 |
0.5 |
0.0 |___________________
    0   20  40  60  80  100
    Label noise (fraction)
```

### After (Sweep - Working):
```
Inverse Coherence
2.5 |
2.0 |
1.5 |  ●────●────●────●────●  (5 points connected)
1.0 |
0.5 |
0.0 |___________________
    0   20  40  60  80  100
    Label noise (fraction)
```

## Quick Fix: Create Minimal Sweep (5 minutes)

**Fastest way to fix**:

1. Go to "Batch Experiments" tab
2. Use these settings:
   ```
   Swept Parameter: aleatoric_noise_percentage
   Values: 0, 50, 100  (just 3 points for speed)
   
   Base Config:
   - Epochs: 1
   - MC passes: 5
   - Under-train: 50
   - Regular-train: 100
   - Eval per group: 50
   ```

3. Click "🚀 Create Batch"

4. Wait ~5 minutes for 3 experiments

5. Refresh visualization → Now shows 3-point line plot ✅

## Why This Happened

The default Streamlit form creates **single experiments**, not sweeps.

To create sweeps, you must use:
- **"Batch Experiments" tab** (manual sweep configuration)
- **Progressive app "Launch fast sweep"** button (pre-configured sweep)
- **Script with loop** (programmatic sweep)

## Verification

After creating sweep, you should see:

```
📊 Experiment Results

Status Metrics:
✅ Completed: 5    📦 Total: 5

Experiments List:
- sweep_noise_0    (completed)
- sweep_noise_25   (completed)
- sweep_noise_50   (completed)
- sweep_noise_75   (completed)
- sweep_noise_100  (completed)

📉 Visualization:
[Shows 5-point line plots for each signal]
```

## Next Steps

1. **Delete single experiment** (optional):
   ```sql
   sqlite3 data/uqlab.db
   DELETE FROM experiments WHERE name = 'exp_20260604_...';
   ```

2. **Create proper sweep** using one of the options above

3. **Verify visualization** shows multiple connected points

4. **Use Smart Experiment Selector** to detect sweep type and create complements

## Prevention

Always use **Batch Experiments** tab or **Progressive app sweeps** for proper visualizations.

Single experiments are only useful for:
- Quick testing
- Debugging
- Single-point analysis

For uncertainty analysis (epistemic vs aleatoric), you NEED sweeps!