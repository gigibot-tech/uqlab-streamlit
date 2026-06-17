# Improved Architecture - Following Folder Flow

## Config Structure (5 Main Keys)

```python
config = {
    "seed": 42,
    "device": "auto",
    "data": {...},      # 1️⃣ Data loading config
    "model": {...},     # 2️⃣ Model architecture config
    "training": {...},  # 3️⃣ Training config
    "evaluation": {...},# 4️⃣ Evaluation config
    "paths": {...}      # File paths
}
```

## Folder Flow = App Flow (1→2→3→4→5→6→7)

```
src/uqlab/
├── 1_data/          # Step 1: Define dataset
├── 2_models/        # Step 2: Define model OR load checkpoint
├── 3_training/      # Step 3: Define training params
├── 4_evaluation/    # Step 4: Define evaluation params
├── 5_api/           # Step 5: Save config, submit to API
├── 6_ui/            # Step 6: Streamlit forms (builds config)
└── 7_orchestration/ # Step 7: Execute script with config
```

## Detailed Flow

### Step 1: Data Configuration (1_data/)

**Purpose**: Define dataset loading parameters

**Folder**: `1_data/`
- `cifar10n_loader.py` - CIFAR-10N dataset class
- `sampling.py` - Under-sampling logic
- `noise_injection.py` - Custom noise injection

**Config Section**: `config["data"]`
```python
{
    "noise_type": "worse_label",           # CIFAR-10N noise type
    "aleatoric_noise_percentage": 0.0,     # Custom noise (overrides CIFAR-10N)
    "under_supported_classes": "3,5",      # Classes with less data
    "under_train_per_class": 50,           # Samples per under-supported class
    "regular_train_per_class": 300,        # Samples per regular class
    "eval_per_group": 600                  # Eval samples per group
}
```

**Streamlit UI** (`6_ui/data_config_form.py`):
```python
def render_data_config():
    """Step 1: Data Configuration Form"""
    st.header("1️⃣ Data Configuration")
    
    # Noise type
    noise_type = st.selectbox("Noise Type", [
        "clean_label", "worse_label", "aggre_label", ...
    ])
    
    # Custom noise (optional)
    use_custom = st.checkbox("Use custom noise instead")
    custom_noise = st.slider("Custom Noise %", 0, 100, 0) if use_custom else 0
    
    # Under-supported classes
    under_classes = st.text_input("Under-supported classes", "3,5")
    under_samples = st.number_input("Samples per under-class", 25, 500, 50)
    regular_samples = st.number_input("Samples per regular class", 100, 1000, 300)
    
    return {
        "noise_type": noise_type,
        "aleatoric_noise_percentage": custom_noise,
        "under_supported_classes": under_classes,
        "under_train_per_class": under_samples,
        "regular_train_per_class": regular_samples,
        "eval_per_group": 600
    }
```

**What `1_data/` does in `run_fast_*.py`**:
```python
# In run_fast_uncertainty_classification.py
from uqlab.1_data.cifar10n_loader import CIFAR10NDataset
from uqlab.1_data.sampling import sample_indices_for_fast_pilot

# Load dataset using config
dataset = CIFAR10NDataset(
    root=config["paths"]["cifar10n_root"],
    noise_type=config["data"]["noise_type"]
)

# Sample indices based on config
train_indices = sample_indices_for_fast_pilot(
    dataset,
    under_supported_classes=config["data"]["under_supported_classes"],
    under_train_per_class=config["data"]["under_train_per_class"],
    regular_train_per_class=config["data"]["regular_train_per_class"]
)
```

### Step 2: Model Configuration (2_models/)

**Purpose**: Define model architecture OR specify checkpoint to load

**Folder**: `2_models/`
- `dinov2_mlp.py` - DINOv2 + MLP classifier
- `resnet.py` - ResNet baseline
- `checkpoints.py` - Load/save checkpoints

**Config Section**: `config["model"]`
```python
{
    "architecture": "dinov2_mlp",          # Model type
    "training_mode": "feature_space",      # Train on features or end-to-end
    "dinov2_model": "small",               # DINOv2 size (small/base/large)
    "hidden_dim": 256,                     # MLP hidden dimension
    "dropout": 0.2,                        # Dropout rate
    "use_untrained_resnet": False,         # Use random ResNet (baseline)
    "checkpoint_path": None                # Optional: load from checkpoint
}
```

**Streamlit UI** (`6_ui/model_config_form.py`):
```python
def render_model_config():
    """Step 2: Model Configuration Form"""
    st.header("2️⃣ Model Configuration")
    
    # Option 1: New model
    # Option 2: Load checkpoint
    mode = st.radio("Model Source", ["New Model", "Load Checkpoint"])
    
    if mode == "New Model":
        architecture = st.selectbox("Architecture", ["dinov2_mlp", "resnet"])
        
        if architecture == "dinov2_mlp":
            dinov2_size = st.selectbox("DINOv2 Size", ["small", "base", "large"])
            hidden_dim = st.number_input("Hidden Dimension", 64, 1024, 256)
            dropout = st.slider("Dropout", 0.0, 0.5, 0.2)
            
            return {
                "architecture": "dinov2_mlp",
                "dinov2_model": dinov2_size,
                "hidden_dim": hidden_dim,
                "dropout": dropout,
                "checkpoint_path": None
            }
    else:
        checkpoint = st.file_uploader("Upload Checkpoint", type=["pt", "pth"])
        return {
            "checkpoint_path": checkpoint.name if checkpoint else None
        }
```

**What `2_models/` does in `run_fast_*.py`**:
```python
from uqlab.2_models.dinov2_mlp import DINOv2MLP
from uqlab.2_models.checkpoints import load_checkpoint

# Option 1: Create new model
if config["model"]["checkpoint_path"] is None:
    model = DINOv2MLP(
        dinov2_model=config["model"]["dinov2_model"],
        hidden_dim=config["model"]["hidden_dim"],
        dropout=config["model"]["dropout"],
        num_classes=10
    )
else:
    # Option 2: Load from checkpoint
    model = load_checkpoint(config["model"]["checkpoint_path"])
```

### Step 3: Training Configuration (3_training/)

**Purpose**: Define training hyperparameters

**Folder**: `3_training/`
- `trainer.py` - Training loop
- `optimizer.py` - Optimizer setup
- `scheduler.py` - Learning rate scheduling

**Config Section**: `config["training"]`
```python
{
    "epochs": 12,                          # Number of epochs
    "learning_rate": 0.001,                # Learning rate
    "weight_decay": 0.0001,                # L2 regularization
    "train_batch_size": 256,               # Training batch size
    "feature_batch_size": 64               # Feature extraction batch size
}
```

**Streamlit UI** (`6_ui/training_config_form.py`):
```python
def render_training_config():
    """Step 3: Training Configuration Form"""
    st.header("3️⃣ Training Configuration")
    
    epochs = st.number_input("Epochs", 1, 100, 12)
    lr = st.number_input("Learning Rate", 0.0001, 0.1, 0.001, format="%.4f")
    weight_decay = st.number_input("Weight Decay", 0.0, 0.01, 0.0001, format="%.4f")
    batch_size = st.selectbox("Batch Size", [64, 128, 256, 512], index=2)
    
    return {
        "epochs": epochs,
        "learning_rate": lr,
        "weight_decay": weight_decay,
        "train_batch_size": batch_size,
        "feature_batch_size": 64
    }
```

**What `3_training/` does in `run_fast_*.py`**:
```python
from uqlab.3_training.trainer import Trainer

# Create trainer with config
trainer = Trainer(
    model=model,
    train_loader=train_loader,
    epochs=config["training"]["epochs"],
    learning_rate=config["training"]["learning_rate"],
    weight_decay=config["training"]["weight_decay"]
)

# Train
trainer.train()
```

### Step 4: Evaluation Configuration (4_evaluation/)

**Purpose**: Define uncertainty quantification and evaluation params

**Folder**: `4_evaluation/`
- `mc_dropout.py` - MC Dropout uncertainty
- `signals.py` - Uncertainty signals
- `metrics.py` - AUROC, accuracy, etc.

**Config Section**: `config["evaluation"]`
```python
{
    "mc_passes": 20,                       # MC Dropout forward passes
    "attribution_method": "dualxda",       # Attribution method
    "top_k": 10                            # Top-K signals to use
}
```

**Streamlit UI** (`6_ui/evaluation_config_form.py`):
```python
def render_evaluation_config():
    """Step 4: Evaluation Configuration Form"""
    st.header("4️⃣ Evaluation Configuration")
    
    mc_passes = st.number_input("MC Dropout Passes", 5, 100, 20)
    attribution = st.selectbox("Attribution Method", ["dualxda", "gradcam", "integrated_gradients"])
    top_k = st.number_input("Top-K Signals", 1, 50, 10)
    
    return {
        "mc_passes": mc_passes,
        "attribution_method": attribution,
        "top_k": top_k
    }
```

**What `4_evaluation/` does in `run_fast_*.py`**:
```python
from uqlab.4_evaluation.mc_dropout import mc_forward_efficient
from uqlab.4_evaluation.signals import SignalCalculator
from uqlab.4_evaluation.metrics import binary_auroc

# MC Dropout
mc_predictions = mc_forward_efficient(
    model,
    eval_loader,
    n_passes=config["evaluation"]["mc_passes"]
)

# Calculate signals
calculator = SignalCalculator()
signals = calculator.calculate_all_signals(mc_predictions)

# Evaluate
auroc = binary_auroc(signals, labels)
```

### Step 5: API Submission (5_api/)

**Purpose**: Save config and submit to backend

**Folder**: `5_api/`
- `experiments.py` - Experiment endpoints
- `batch.py` - Batch experiment endpoints

**What happens**: Config is complete, send to API

**Streamlit UI** (`6_ui/submit_form.py`):
```python
def render_submit_form(config):
    """Step 5: Submit Configuration"""
    st.header("5️⃣ Submit Experiment")
    
    # Show complete config
    st.json(config)
    
    # Submit options
    exp_name = st.text_input("Experiment Name", f"exp_{timestamp}")
    auto_start = st.checkbox("Start immediately", value=True)
    
    if st.button("Submit to API"):
        client = ExperimentAPIClient(API_URL)
        exp = client.create_experiment(exp_name, config)
        
        if auto_start:
            client.start_experiment(exp["id"])
        
        st.success(f"Experiment {exp['id']} created!")
```

### Step 6: UI Layer (6_ui/)

**Purpose**: Streamlit forms that build the config step-by-step

**Folder**: `6_ui/`
- `data_config_form.py` - Step 1 form
- `model_config_form.py` - Step 2 form
- `training_config_form.py` - Step 3 form
- `evaluation_config_form.py` - Step 4 form
- `submit_form.py` - Step 5 submission
- `results_viewer.py` - Display results
- `visualizations.py` - Plot results

**Main App** (`streamlit_app_progressive.py`):
```python
def main():
    st.title("Uncertainty Quantification Experiment Builder")
    
    # Initialize config
    if "config" not in st.session_state:
        st.session_state.config = {
            "seed": 42,
            "device": "auto",
            "data": {},
            "model": {},
            "training": {},
            "evaluation": {},
            "paths": {
                "cifar10n_root": "./data/cifar10n",
                "feature_cache_dir": "./cache/features",
                "results_base_dir": "./results"
            }
        }
    
    # Step 1: Data Config
    st.session_state.config["data"] = render_data_config()
    
    # Step 2: Model Config
    st.session_state.config["model"] = render_model_config()
    
    # Step 3: Training Config
    st.session_state.config["training"] = render_training_config()
    
    # Step 4: Evaluation Config
    st.session_state.config["evaluation"] = render_evaluation_config()
    
    # Step 5: Submit
    render_submit_form(st.session_state.config)
    
    # Step 6: View Results
    render_results_viewer()
```

### Step 7: Orchestration (7_orchestration/)

**Purpose**: Execute the script with the config

**Folder**: `7_orchestration/`
- `experiment_runner.py` - Runs single experiments
- `batch_runner.py` - Runs batch sweeps
- `storage.py` - Saves results

**What happens**: Script is called with config

```python
# 7_orchestration/experiment_runner.py
class ExperimentRunner:
    def run_experiment(self, config: Dict) -> Dict:
        """Run experiment by calling script"""
        # Save config to temp file
        config_path = save_temp_config(config)
        
        # Call script
        result = subprocess.run([
            "python", "scripts/run_fast_uncertainty_classification.py",
            "--config", config_path
        ], capture_output=True)
        
        # Load results
        results = load_results(config["paths"]["results_base_dir"])
        return results
```

## Summary: Config Has 5 Main Keys

```python
config = {
    # Top-level
    "seed": 42,
    "device": "auto",
    
    # 1️⃣ Data (from 1_data/)
    "data": {
        "noise_type": "worse_label",
        "aleatoric_noise_percentage": 0.0,
        "under_supported_classes": "3,5",
        "under_train_per_class": 50,
        "regular_train_per_class": 300,
        "eval_per_group": 600
    },
    
    # 2️⃣ Model (from 2_models/)
    "model": {
        "architecture": "dinov2_mlp",
        "dinov2_model": "small",
        "hidden_dim": 256,
        "dropout": 0.2,
        "checkpoint_path": None  # OR path to load
    },
    
    # 3️⃣ Training (from 3_training/)
    "training": {
        "epochs": 12,
        "learning_rate": 0.001,
        "weight_decay": 0.0001,
        "train_batch_size": 256,
        "feature_batch_size": 64
    },
    
    # 4️⃣ Evaluation (from 4_evaluation/)
    "evaluation": {
        "mc_passes": 20,
        "attribution_method": "dualxda",
        "top_k": 10
    },
    
    # Paths
    "paths": {
        "cifar10n_root": "./data/cifar10n",
        "feature_cache_dir": "./cache/features",
        "results_base_dir": "./results"
    }
}
```

## Flow Diagram

```
User Opens Streamlit
        ↓
┌───────────────────────────────────────┐
│ 6_ui/ (Streamlit Forms)              │
│                                       │
│  Step 1: render_data_config()        │ → config["data"]
│  Step 2: render_model_config()       │ → config["model"]
│  Step 3: render_training_config()    │ → config["training"]
│  Step 4: render_evaluation_config()  │ → config["evaluation"]
│  Step 5: render_submit_form()        │ → Submit to API
└───────────────────────────────────────┘
        ↓
┌───────────────────────────────────────┐
│ 5_api/ (FastAPI Backend)             │
│  - Receives config                    │
│  - Stores in database                 │
│  - Calls orchestrator                 │
└───────────────────────────────────────┘
        ↓
┌───────────────────────────────────────┐
│ 7_orchestration/ (Experiment Runner) │
│  - Calls run_fast_*.py script         │
│  - Passes config as argument          │
└───────────────────────────────────────┘
        ↓
┌───────────────────────────────────────┐
│ scripts/run_fast_*.py (Executor)      │
│                                       │
│  1_data/    → Load dataset            │
│  2_models/  → Create/load model       │
│  3_training/→ Train model             │
│  4_evaluation/→ Evaluate & compute    │
│                                       │
│  Save results to disk                 │
└───────────────────────────────────────┘
        ↓
┌───────────────────────────────────────┐
│ 6_ui/ (Results Viewer)               │
│  - Load results from disk/API         │
│  - Render plots                       │
│  - Show metrics                       │
└───────────────────────────────────────┘
```

## Key Insights

1. **Folder numbers = execution order** (1→2→3→4)
2. **Each folder = one config section** (data, model, training, evaluation)
3. **6_ui/ builds config** (forms for each section)
4. **7_orchestration/ executes** (calls script with config)
5. **scripts/ use folders 1-4** (in order: data → model → training → evaluation)

This makes the codebase **self-documenting** - the folder structure tells you the execution flow!