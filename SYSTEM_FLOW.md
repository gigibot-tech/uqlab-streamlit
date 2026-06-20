# 🔄 UQLab System Flow - The Complete Picture

**Last Updated:** 2026-06-18  
**Purpose:** Crystal-clear explanation of how everything fits together

---

## 🎯 THE CORE: What Actually Runs Experiments?

**YES, you're right!** The core is:

```
scripts/run_fast_uncertainty_classification.py
```

This is the **ACTUAL EXPERIMENT RUNNER** that:
1. Loads CIFAR-10N data
2. Trains models (DINOv2 + MLP, ResNet, CNN)
3. Runs MC Dropout for uncertainty
4. Calculates 20+ uncertainty signals
5. Saves results to disk

**Everything else is orchestration, UI, or analysis.**

---

## 📊 THE COMPLETE FLOW (Simplified)

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERACTION                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              STREAMLIT UI (Frontend)                         │
│  streamlit_app_progressive.py                                │
│  • Configure experiment parameters                           │
│  • Click "Run Experiment"                                    │
│  • View results in real-time                                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              FASTAPI BACKEND (Orchestrator)                  │
│  backend/app/main.py                                         │
│  • Receives experiment config via REST API                   │
│  • Validates parameters                                      │
│  • Stores in PostgreSQL database                             │
│  • Launches experiment subprocess                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│         🎯 CORE EXPERIMENT RUNNER (The Real Work)            │
│  scripts/run_fast_uncertainty_classification.py              │
│                                                              │
│  1️⃣ DATA LOADING                                            │
│     └─ src/uqlab/1_data/                                     │
│        • Load CIFAR-10N with label noise                     │
│        • Split into clean/aleatoric/epistemic groups         │
│        • Apply transforms (DINOv2 preprocessing)             │
│                                                              │
│  2️⃣ MODEL BUILDING                                          │
│     └─ src/uqlab/2_models/                                   │
│        • DINOv2 feature extractor (frozen)                   │
│        • MLP classifier with MC Dropout                      │
│        • OR ResNet18 with MC Dropout                         │
│        • OR Custom CNN with MC Dropout                       │
│                                                              │
│  3️⃣ TRAINING                                                │
│     └─ src/uqlab/3_training/                                 │
│        • Train on selected samples                           │
│        • Save checkpoints                                    │
│        • Log metrics                                         │
│                                                              │
│  4️⃣ UNCERTAINTY QUANTIFICATION                              │
│     └─ src/uqlab/4_evaluation/                               │
│        • Run MC Dropout (20 forward passes)                  │
│        • Calculate 20+ uncertainty signals:                  │
│          - Predictive entropy                                │
│          - Mutual information (epistemic)                    │
│          - Expected entropy (aleatoric)                      │
│          - Variance, std, max_prob, etc.                     │
│        • Compute AUROC for each signal                       │
│                                                              │
│  5️⃣ SAVE RESULTS                                            │
│     └─ outputs/                                              │
│        • summary.json (metrics, AUROC scores)                │
│        • per_sample.csv (predictions + uncertainties)        │
│        • model.pth (trained weights)                         │
│        • config.yaml (experiment config)                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              RESULTS STORAGE & RETRIEVAL                     │
│  • PostgreSQL: Experiment metadata                           │
│  • Filesystem: Model weights, CSVs, plots                    │
│  • Backend API: Fetch results for UI                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              VISUALIZATION (Back to UI)                      │
│  src/uqlab/ui_components/visualization/                      │
│  • Plot accuracy vs label noise                              │
│  • Show uncertainty decomposition                            │
│  • Display signal AUROC heatmaps                             │
│  • Render 2D parameter sweeps                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔑 KEY COMPONENTS EXPLAINED

### 1. **The Core Runner** (Where Magic Happens)
**File:** `scripts/run_fast_uncertainty_classification.py`

**What it does:**
```python
# Pseudocode of what happens inside
def run_experiment(config):
    # 1. Load data
    dataset = load_cifar10n(noise_type="worse_label")
    train_data, eval_data = split_data(dataset, config)
    
    # 2. Build model
    model = build_model(
        architecture="dinov2_mlp",  # or resnet18, cnn
        dropout=0.3,
        hidden_dim=256
    )
    
    # 3. Train
    for epoch in range(config.epochs):
        train_one_epoch(model, train_data)
    
    # 4. Evaluate with MC Dropout
    uncertainties = []
    for _ in range(20):  # MC passes
        predictions = model(eval_data, dropout=True)
        uncertainties.append(predictions)
    
    # 5. Calculate signals
    signals = {
        "predictive_entropy": calculate_entropy(uncertainties),
        "mutual_info": calculate_mutual_info(uncertainties),
        "expected_entropy": calculate_expected_entropy(uncertainties),
        # ... 17 more signals
    }
    
    # 6. Compute AUROC
    aurocs = {}
    for signal_name, signal_values in signals.items():
        aurocs[signal_name] = binary_auroc(
            signal_values, 
            ground_truth_labels
        )
    
    # 7. Save everything
    save_results(aurocs, signals, model)
    
    return aurocs
```

**Input:** Experiment config (JSON/dict)  
**Output:** Results directory with metrics, CSVs, model weights

---

### 2. **The Orchestrator** (Manages Experiments)
**File:** `src/uqlab/7_orchestration/`

**What it does:**
- Generates sweep configurations (e.g., dropout=[0.1, 0.2, 0.3])
- Launches multiple experiments in parallel
- Tracks experiment status
- Aggregates results

**Example:**
```python
# User wants to sweep dropout values
sweep_config = {
    "base_config": {...},
    "sweep_parameter": "dropout",
    "sweep_values": [0.1, 0.2, 0.3, 0.4, 0.5]
}

# Orchestrator generates 5 experiment configs
for dropout_val in sweep_values:
    config = copy(base_config)
    config["dropout"] = dropout_val
    launch_experiment(config)  # Calls run_fast_uncertainty_classification.py
```

---

### 3. **The UI** (User Interface)
**File:** `streamlit_app_progressive.py`

**What it does:**
- Renders forms for experiment configuration
- Sends configs to backend API
- Polls for results
- Displays plots and tables

**Flow:**
```
User fills form → Click "Run" → POST to /api/v1/experiments 
→ Backend launches subprocess → UI polls /api/v1/experiments/{id}
→ Display results when complete
```

---

### 4. **The Backend** (REST API)
**File:** `backend/app/main.py`

**What it does:**
- Exposes REST API endpoints
- Validates experiment configs
- Stores metadata in PostgreSQL
- Launches experiment subprocesses
- Serves results to UI

**Key Endpoints:**
```
POST   /api/v1/experiments          # Create experiment
GET    /api/v1/experiments          # List experiments
GET    /api/v1/experiments/{id}     # Get experiment details
POST   /api/v1/batch-experiments    # Create batch sweep
GET    /api/v1/batch-experiments    # List batches
```

---

## 🎨 DATA FLOW DIAGRAM

```
┌──────────┐
│   USER   │
└────┬─────┘
     │ 1. Configure experiment
     ▼
┌─────────────────┐
│  STREAMLIT UI   │
└────┬────────────┘
     │ 2. POST /api/v1/experiments
     ▼
┌─────────────────┐
│  FASTAPI BACKEND│
└────┬────────────┘
     │ 3. subprocess.run(run_fast_uncertainty_classification.py)
     ▼
┌──────────────────────────────────────────┐
│  CORE RUNNER                             │
│  ┌────────┐  ┌────────┐  ┌────────┐     │
│  │ Data   │→ │ Model  │→ │ Train  │     │
│  └────────┘  └────────┘  └────────┘     │
│       ↓                                  │
│  ┌────────┐  ┌────────┐  ┌────────┐     │
│  │ MC     │→ │ Signals│→ │ AUROC  │     │
│  │ Dropout│  │        │  │        │     │
│  └────────┘  └────────┘  └────────┘     │
└──────────────────┬───────────────────────┘
                   │ 4. Save results
                   ▼
┌──────────────────────────────────────────┐
│  STORAGE                                 │
│  • PostgreSQL (metadata)                 │
│  • Filesystem (outputs/)                 │
└──────────────────┬───────────────────────┘
                   │ 5. Fetch results
                   ▼
┌──────────────────────────────────────────┐
│  VISUALIZATION                           │
│  • Plots (matplotlib, plotly)            │
│  • Tables (pandas)                       │
│  • Metrics (AUROC, accuracy)             │
└──────────────────────────────────────────┘
```

---

## 📁 DIRECTORY STRUCTURE (Simplified)

```
uqlab-streamlit/
│
├── scripts/
│   └── run_fast_uncertainty_classification.py  ← 🎯 THE CORE
│
├── src/uqlab/                                  ← ML Framework
│   ├── 1_data/          # Data loaders
│   ├── 2_models/        # Model architectures
│   ├── 3_training/      # Training loops
│   ├── 4_evaluation/    # Uncertainty metrics
│   ├── 5_api/           # watsonx.ai integration
│   ├── 7_orchestration/ # Experiment management
│   └── ui_components/   # Streamlit widgets
│
├── backend/                                    ← REST API
│   └── app/
│       ├── api/         # Endpoints
│       ├── models.py    # Database models
│       └── main.py      # FastAPI app
│
├── streamlit_app_progressive.py                ← UI Entry Point
│
└── outputs/                                    ← Results Storage
    └── exp_20260618_123456/
        ├── summary.json
        ├── per_sample.csv
        ├── model.pth
        └── config.yaml
```

---

## 🚀 EXECUTION PATHS

### Path 1: Single Experiment via UI
```
1. User: Open streamlit_app_progressive.py
2. User: Fill form (dataset, model, training params)
3. User: Click "Run Experiment"
4. UI: POST to backend /api/v1/experiments
5. Backend: Validate config, save to DB
6. Backend: subprocess.run(run_fast_uncertainty_classification.py)
7. Core: Run experiment, save results
8. Backend: Update DB with status="completed"
9. UI: Poll backend, display results
```

### Path 2: Batch Sweep via UI
```
1. User: Configure base experiment
2. User: Select sweep parameter (e.g., "dropout")
3. User: Set sweep range (0.1 to 0.5, step 0.1)
4. UI: POST to backend /api/v1/batch-experiments
5. Backend: Generate 5 experiment configs
6. Backend: Launch 5 subprocesses (parallel or sequential)
7. Core: Run each experiment
8. Backend: Aggregate results
9. UI: Display heatmap of dropout vs AUROC
```

### Path 3: Direct Script Execution (No UI)
```bash
# Run experiment directly from command line
python scripts/run_fast_uncertainty_classification.py \
    --dataset cifar10n \
    --noise-type worse_label \
    --architecture dinov2_mlp \
    --dropout 0.3 \
    --epochs 12 \
    --output-dir outputs/my_experiment
```

---

## 🔍 WHAT HAPPENS DURING AN EXPERIMENT?

### Timeline (Typical 12-epoch experiment)

```
00:00 - Load CIFAR-10N dataset (50,000 images)
00:30 - Split into train/eval groups
01:00 - Initialize DINOv2 feature extractor (frozen)
01:30 - Build MLP classifier (256 hidden, 0.3 dropout)
02:00 - Start training (12 epochs)
        ├─ Epoch 1: Loss=2.1, Acc=25%
        ├─ Epoch 2: Loss=1.8, Acc=35%
        ├─ ...
        └─ Epoch 12: Loss=0.4, Acc=85%
10:00 - Training complete
10:30 - Run MC Dropout evaluation (20 passes)
        ├─ Pass 1: Get predictions
        ├─ Pass 2: Get predictions
        ├─ ...
        └─ Pass 20: Get predictions
15:00 - Calculate 20+ uncertainty signals
        ├─ Predictive entropy
        ├─ Mutual information
        ├─ Expected entropy
        ├─ Variance, std, max_prob
        └─ ... (17 more)
18:00 - Compute AUROC for each signal
        ├─ Epistemic AUROC: 0.75
        ├─ Aleatoric AUROC: 0.68
        └─ ... (18 more)
20:00 - Save results to disk
        ├─ summary.json
        ├─ per_sample.csv (50,000 rows)
        ├─ model.pth
        └─ config.yaml
20:30 - DONE ✅
```

---

## 🎓 KEY CONCEPTS

### 1. **Uncertainty Decomposition**
```
Total Uncertainty = Epistemic + Aleatoric

Epistemic (Model Uncertainty):
  - "I don't know because I haven't seen enough data"
  - Measured by: mutual_info
  - Reducible with more training data

Aleatoric (Data Uncertainty):
  - "I don't know because the data is inherently noisy"
  - Measured by: expected_entropy
  - Irreducible (inherent in data)

Formula:
  predictive_entropy = mutual_info + expected_entropy
```

### 2. **MC Dropout**
```python
# Standard inference (dropout OFF)
prediction = model(x, dropout=False)  # Single prediction

# MC Dropout (dropout ON during inference)
predictions = []
for _ in range(20):
    pred = model(x, dropout=True)  # Different each time
    predictions.append(pred)

# Uncertainty = variance across predictions
uncertainty = np.var(predictions, axis=0)
```

### 3. **AUROC (Area Under ROC Curve)**
```
Measures how well a signal separates two groups:
- AUROC = 1.0: Perfect separation
- AUROC = 0.5: Random guessing
- AUROC = 0.0: Perfect inverse separation

Example:
  Epistemic AUROC = 0.75
  → Signal correctly identifies epistemic samples 75% of the time
```

---

## 🎯 SIMPLICITY CHECK

**Q: Is the flow as simple as it can be?**

**A: Almost, but there's room for improvement:**

### Current Complexity:
1. ✅ **Core runner is simple** - One script does the work
2. ⚠️ **Orchestration adds layers** - Backend, API, database
3. ⚠️ **UI has multiple entry points** - streamlit_app.py vs streamlit_app_progressive.py
4. ⚠️ **Results storage is split** - PostgreSQL + filesystem

### Simplification Opportunities:
1. **Merge UI files** - Single streamlit_app.py with tabs
2. **Optional backend** - Allow direct script execution without API
3. **Unified storage** - Store everything in one place (DB or filesystem)
4. **Clearer naming** - Rename files to show hierarchy

### Ideal Simple Flow:
```
User → Streamlit UI → run_fast_uncertainty_classification.py → Results
```

**Current flow has more steps, but they enable:**
- Multi-user support (backend + DB)
- Parallel experiments (orchestration)
- Real-time monitoring (API polling)
- Result persistence (database)

**Trade-off:** Complexity vs Features

---

## 📚 RELATED DOCUMENTATION

- **Core Runner Details:** `scripts/run_fast_uncertainty_classification.py` (docstring)
- **Model Architectures:** `src/uqlab/2_models/README.md`
- **UI Components:** `src/uqlab/ui_components/README.md`
- **Plot Inventory:** `UI_PLOT_INVENTORY.md`
- **Architecture Guide:** `.bob/skills/architecture-aware-refactoring.md`

---

**End of System Flow Documentation**