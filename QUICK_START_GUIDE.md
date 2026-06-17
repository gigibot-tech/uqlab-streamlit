# Quick Start Guide - Getting Experiments to Show

## Current Status
```
✅ API online
❌ 0 experiments in DB (/Users/andrearachetta/Documents/old_pilots/uqlab-streamlit/data/uqlab.db)
```

## How Experiments Appear in Streamlit

### Main Screen Layout

```
┌─────────────────────────────────────────────────────────────┐
│  🔬 Uncertainty Quantification Experiment Configuration     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📊 Dataset Selection & Overview                            │
│  [CIFAR-10N] [worse_label]                                  │
│                                                             │
│  ⚙️ Configuration Forms                                     │
│  - Epistemic Uncertainty                                    │
│  - Aleatoric Uncertainty                                    │
│  - Model & Training                                         │
│  - Evaluation                                               │
│                                                             │
│  [🚀 Create Experiment]  ← Click here to create!           │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  📋 Experiment Results                                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ No experiments yet. Create one above!               │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Right Sidebar (Configuration Progress)

```
┌──────────────────────────────┐
│ ✅ Logged in as:             │
│    test@example.com          │
│                              │
│ ─────────────────────────    │
│                              │
│ ⚙️ Configuration Progress    │
│                              │
│ ✅ Dataset Selected          │
│ ⏳ Epistemic Config          │
│ ⏳ Aleatoric Config          │
│ ⏳ Model Config              │
│ ⏳ Evaluation Config         │
│                              │
│ 🔗 API Status                │
│ ✅ Connected                 │
│ http://localhost:8000        │
└──────────────────────────────┘
```

## Step-by-Step: Create Your First Experiment

### Step 1: Fill Configuration (Main Screen)

1. **Dataset** (already selected): CIFAR-10N with worse_label
2. **Epistemic Uncertainty**:
   - Under-supported classes: `random:2` (2 random classes)
   - Under-train samples: `50` per class
   - Regular samples: `300` per class

3. **Aleatoric Uncertainty**:
   - Noise source: "Use CIFAR-10N noise" OR "Custom noise"
   - Custom noise rate: `0%` (if custom)

4. **Model & Training**:
   - Model: `dinov2-small`
   - Hidden dim: `256`
   - Dropout: `0.2`
   - Epochs: `2` (quick test) or `12` (full)
   - Learning rate: `0.001`
   - Batch size: `256`

5. **Evaluation**:
   - MC passes: `10` (quick) or `20` (full)
   - Eval per group: `100`
   - Signals: Select 4-6 signals

### Step 2: Click "🚀 Create Experiment"

The form will submit and you'll see:
```
✅ Experiment created: exp_20260604_223000
ℹ️ Experiment ID: abc123...
ℹ️ Status: queued
```

### Step 3: Experiments Appear Below

After creation, the **📋 Experiment Results** section updates:

```
📋 Experiment Results

Status Metrics:
⏸️ Queued: 1    ▶️ Running: 0    ✅ Completed: 0    ❌ Failed: 0    📦 Total: 1

Experiments List:
┌────────────────────────────────────────────────────────────┐
│ exp_20260604_223000                                        │
│ Status: queued → running → completed                       │
│ Progress: ████████░░ 80%                                   │
│                                                            │
│ [View Details] [View Results]                              │
└────────────────────────────────────────────────────────────┘
```

### Step 4: Auto-Refresh (Optional)

Enable auto-refresh to see progress updates:
```
☑️ Auto-refresh results (every 5s)
```

## Where Experiments Are Stored

### 1. Database (SQLite)
```
/Users/andrearachetta/Documents/old_pilots/uqlab-streamlit/data/uqlab.db
```

**Tables**:
- `experiments` - Experiment metadata
- `batch_experiments` - Batch sweep configurations

### 2. Results Files (Disk)
```
/tmp/uqlab_experiments/{experiment_id}/
├── results/
│   ├── per_sample_signals.csv    ← Signal values per sample
│   ├── summary.json               ← Accuracy, AUROC, etc.
│   └── model_checkpoint.pt        ← Trained model
└── logs/
    └── training.log
```

## How to Populate with Experiments

### Option A: Create Single Experiment (Streamlit UI)

1. Open Streamlit: `streamlit run streamlit_app_progressive.py`
2. Fill configuration form
3. Click "🚀 Create Experiment"
4. Wait for completion (~5-10 min for quick config)

### Option B: Create Batch Sweep (Streamlit UI)

1. Go to "Batch Experiments" tab
2. Configure sweep:
   - Parameter: `aleatoric_noise_percentage`
   - Values: `[0, 25, 50, 75, 100]`
3. Click "🚀 Create Batch Experiment"
4. Creates 5 experiments automatically

### Option C: Use Validation Presets (Notebooks)

```bash
cd uqlab-streamlit/notebooks/validation
jupyter lab architecture_comparison_label_noise.ipynb
```

These notebooks have pre-configured sweeps that populate `results/validation/`

### Option D: Run Script Directly

```bash
cd uqlab-streamlit
source .venv/bin/activate

python scripts/run_fast_uncertainty_classification.py \
  --noise-type worse_label \
  --under-supported "random:2" \
  --under-train-per-class 50 \
  --regular-train-per-class 300 \
  --epochs 2 \
  --mc-passes 10
```

## Troubleshooting: "0 experiments in DB"

### Check 1: Is API Running?

```bash
# Terminal 1: Start API
cd uqlab-streamlit/backend
uvicorn app.main:app --reload

# Terminal 2: Check API
curl http://localhost:8000/api/v1/experiments/no-auth
# Should return: []
```

### Check 2: Database Exists?

```bash
ls -la /Users/andrearachetta/Documents/old_pilots/uqlab-streamlit/data/uqlab.db
# Should show file with size > 0
```

If missing:
```bash
cd uqlab-streamlit/backend
alembic upgrade head  # Creates tables
```

### Check 3: Create Test Experiment

```bash
curl -X POST http://localhost:8000/api/v1/experiments/no-auth \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test_exp",
    "config": {
      "noise_type": "worse_label",
      "under_supported": "random:2",
      "epochs": 2
    }
  }'
```

Should return experiment JSON with ID.

### Check 4: Refresh Streamlit

After creating via API/script:
1. Go back to Streamlit
2. Click "🔄 Refresh" or enable auto-refresh
3. Experiments should appear

## Expected Workflow

```
1. Start API (backend)
   ↓
2. Open Streamlit (frontend)
   ↓
3. See "0 experiments" initially ← YOU ARE HERE
   ↓
4. Create experiment via form
   ↓
5. Experiment appears in list (status: queued)
   ↓
6. Training starts (status: running)
   ↓
7. Progress bar updates
   ↓
8. Training completes (status: completed)
   ↓
9. Results appear (plots, metrics, signals)
   ↓
10. Create more experiments or sweeps
```

## Quick Test: Create Minimal Experiment

**Fastest way to see experiments appear**:

1. In Streamlit, use these minimal settings:
   ```
   Epochs: 1
   MC passes: 5
   Eval per group: 50
   Under-train: 50
   Regular-train: 100
   ```

2. Click "🚀 Create Experiment"

3. Should complete in ~2-3 minutes

4. Experiment will appear in list below

## Next Steps

Once you have experiments:
- Use **Smart Experiment Selector** to detect sweep type
- Create complementary sweeps for 2D visualization
- View per-signal AUROC plots
- Compare epistemic vs aleatoric uncertainty

Need help? Check:
- `EPISTEMIC_UNCERTAINTY_EXPLAINED.md` - Understanding uncertainty values
- `SMART_EXPERIMENT_SELECTOR_IMPLEMENTATION.md` - Advanced visualization
- `VISUALIZATION_FIX_PLAN.md` - Plot interpretation