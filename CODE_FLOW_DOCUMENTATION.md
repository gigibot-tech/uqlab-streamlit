# Code Flow Documentation - Jupyter Notebook Style

This document shows the code execution flow through the walaris-cen codebase, similar to how you'd see it in a Jupyter notebook with clear cell-by-cell execution.

## 📊 Overview: How Everything Connects

```
streamlit_app.py
    ↓
ui_components/
    ↓
backend/app/api/routes/
    ↓
src/data/ & src/walaris/
    ↓
Training & Evaluation
```

---

## 🔬 Cell 1: Streamlit App Entry Point

**File**: `streamlit_app.py` (or `streamlit_app_progressive.py`)

```python
# CELL 1: Initialize Streamlit App
import streamlit as st
import requests
from ui_components import (
    build_base_experiment_config,
    render_dataset_selection,
    # ... other UI components
)

# Configuration
API_BASE_URL = "http://localhost:8000"

# Main app logic
def main():
    st.title("🔬 Uncertainty Quantification")
    
    # Step 1: Dataset Selection
    dataset_name, noise_type, stats = render_dataset_selection(...)
```

**What happens here:**
- User interacts with Streamlit UI
- Selects dataset, model, uncertainty parameters
- Calls UI component functions

---

## 🎨 Cell 2: UI Components Layer

**File**: `ui_components/experiment_config.py`

```python
# CELL 2: UI Components - Dataset Selection
def render_dataset_selection(default_dataset, default_noise, fetch_stats_fn):
    """
    Renders dataset selection UI and fetches stats from backend
    """
    dataset = st.selectbox("Dataset", ["cifar10"])
    noise_type = st.selectbox("Noise", ["none", "worse_label", ...])
    
    # Call backend API through fetch_stats_fn
    stats = fetch_stats_fn(dataset, noise_type)
    
    return dataset, noise_type, stats
```

**What happens here:**
- Renders Streamlit widgets (selectbox, sliders, etc.)
- Collects user input
- Calls backend API functions
- Returns configuration data

**File**: `ui_components/experiment_config.py`

```python
# CELL 2B: Build Experiment Configuration
def build_base_experiment_config(
    noise_type,
    under_supported,
    under_train_per_class,
    regular_train_per_class,
    dinov2_model,
    hidden_dim,
    dropout,
    epochs,
    learning_rate,
    # ... more parameters
):
    """
    Builds complete experiment configuration dictionary
    """
    return {
        "dataset": {
            "name": "cifar10",
            "noise_type": noise_type,
            "under_supported_classes": under_supported,
            "under_train_per_class": under_train_per_class,
            "regular_train_per_class": regular_train_per_class,
        },
        "model": {
            "architecture": dinov2_model,
            "hidden_dim": hidden_dim,
            "dropout": dropout,
        },
        "training": {
            "epochs": epochs,
            "learning_rate": learning_rate,
        },
        # ... more config sections
    }
```

**What happens here:**
- Takes all user inputs
- Organizes them into structured config dict
- Returns config ready for backend API

---

## 🌐 Cell 3: Backend API Call

**File**: `streamlit_app.py`

```python
# CELL 3: Send Experiment to Backend
def create_experiment(config):
    """
    POST request to FastAPI backend
    """
    experiment_data = {
        "name": "exp_20260604_123456",
        "config": config
    }
    
    response = requests.post(
        f"{API_BASE_URL}/api/v1/experiments/no-auth",
        json=experiment_data,
        timeout=30
    )
    
    return response.json()
```

**What happens here:**
- Sends HTTP POST to FastAPI backend
- Backend receives experiment configuration
- Returns experiment ID and status

---

## 🔌 Cell 4: Backend API Routes

**File**: `backend/app/api/routes/experiments.py`

```python
# CELL 4: FastAPI Endpoint
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()

@router.post("/experiments/no-auth")
async def create_experiment_no_auth(
    experiment: ExperimentCreate,
    db: Session = Depends(get_db)
):
    """
    Creates new experiment in database
    Triggers training pipeline
    """
    # 1. Save to database
    db_experiment = Experiment(
        name=experiment.name,
        config=experiment.config,
        status="pending"
    )
    db.add(db_experiment)
    db.commit()
    
    # 2. Trigger training (async or celery task)
    # trigger_training_pipeline(db_experiment.id, experiment.config)
    
    return db_experiment
```

**What happens here:**
- Receives experiment config from Streamlit
- Saves to PostgreSQL database
- Triggers training pipeline (async)
- Returns experiment record

**File**: `backend/app/api/routes/datasets.py`

```python
# CELL 4B: Dataset Stats Endpoint
@router.get("/datasets/{dataset_name}/stats")
async def get_dataset_stats(
    dataset_name: str,
    noise_type: str = "none"
):
    """
    Returns dataset statistics
    """
    # Load dataset using data loader
    from src.data.cifar10n_loader import CIFAR10NDataset
    
    dataset = CIFAR10NDataset(
        root="./data",
        noise_type=noise_type,
        train=True
    )
    
    # Calculate statistics
    stats = {
        "total_samples": len(dataset),
        "num_classes": 10,
        "noise_rate": dataset.get_noise_rate(),
        "class_distribution": dataset.get_class_distribution(),
    }
    
    return stats
```

**What happens here:**
- Receives dataset query from Streamlit
- Loads dataset using data loader
- Calculates statistics
- Returns to frontend

---

## 📦 Cell 5: Data Loading Layer

**File**: `src/data/cifar10n_loader.py`

```python
# CELL 5: CIFAR-10N Dataset Loader
from torch.utils.data import Dataset
import numpy as np
import pickle

class CIFAR10NDataset(Dataset):
    """
    Loads CIFAR-10 with noisy labels
    """
    def __init__(self, root, noise_type="worse_label", train=True):
        self.root = root
        self.noise_type = noise_type
        self.train = train
        
        # Load CIFAR-10 data
        self.data, self.targets = self._load_cifar10()
        
        # Load noisy labels if specified
        if noise_type != "none":
            self.noisy_labels = self._load_noisy_labels()
    
    def _load_cifar10(self):
        """Load original CIFAR-10 data"""
        data_path = f"{self.root}/cifar-10-batches-py"
        
        # Load all batches
        data_list = []
        labels_list = []
        
        for i in range(1, 6):
            with open(f"{data_path}/data_batch_{i}", 'rb') as f:
                batch = pickle.load(f, encoding='bytes')
                data_list.append(batch[b'data'])
                labels_list.append(batch[b'labels'])
        
        data = np.vstack(data_list)
        labels = np.concatenate(labels_list)
        
        return data, labels
    
    def _load_noisy_labels(self):
        """Load CIFAR-10N noisy labels"""
        noise_file = f"{self.root}/CIFAR-10_human.pt"
        noise_data = torch.load(noise_file)
        return noise_data[self.noise_type]
    
    def __getitem__(self, idx):
        """Get single sample"""
        img = self.data[idx]
        target = self.targets[idx]
        
        if self.noise_type != "none":
            noisy_target = self.noisy_labels[idx]
            return img, target, noisy_target
        
        return img, target
    
    def __len__(self):
        return len(self.data)
```

**What happens here:**
- Loads CIFAR-10 images from disk
- Loads noisy labels if specified
- Provides PyTorch Dataset interface
- Used by training pipeline

---

## 🧠 Cell 6: Model Architecture

**File**: `src/walaris/classification/models.py`

```python
# CELL 6: Model Definition
import torch
import torch.nn as nn
from transformers import AutoModel

class DINOv2Classifier(nn.Module):
    """
    DINOv2 backbone + classification head
    """
    def __init__(self, model_name="dinov2-small", num_classes=10, hidden_dim=256, dropout=0.2):
        super().__init__()
        
        # Load pre-trained DINOv2
        self.backbone = AutoModel.from_pretrained(
            f"facebook/{model_name}"
        )
        
        # Freeze backbone (optional)
        for param in self.backbone.parameters():
            param.requires_grad = False
        
        # Classification head
        self.classifier = nn.Sequential(
            nn.Linear(self.backbone.config.hidden_size, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, num_classes)
        )
    
    def forward(self, x):
        """Forward pass"""
        # Extract features from DINOv2
        features = self.backbone(x).last_hidden_state[:, 0]  # CLS token
        
        # Classify
        logits = self.classifier(features)
        
        return logits
```

**What happens here:**
- Defines neural network architecture
- Uses pre-trained DINOv2 as feature extractor
- Adds classification head
- Returns logits for uncertainty quantification

---

## 🏋️ Cell 7: Training Pipeline

**File**: `scripts/run_fast_uncertainty_classification.py`

```python
# CELL 7: Training Loop
def train_model(config):
    """
    Main training function
    """
    # 1. Load dataset
    from src.data.cifar10n_loader import CIFAR10NDataset
    
    train_dataset = CIFAR10NDataset(
        root="./data",
        noise_type=config["dataset"]["noise_type"],
        train=True
    )
    
    train_loader = DataLoader(
        train_dataset,
        batch_size=config["training"]["batch_size"],
        shuffle=True
    )
    
    # 2. Initialize model
    from src.walaris.classification.models import DINOv2Classifier
    
    model = DINOv2Classifier(
        model_name=config["model"]["architecture"],
        num_classes=10,
        hidden_dim=config["model"]["hidden_dim"],
        dropout=config["model"]["dropout"]
    )
    
    # 3. Training loop
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=config["training"]["learning_rate"]
    )
    criterion = nn.CrossEntropyLoss()
    
    for epoch in range(config["training"]["epochs"]):
        model.train()
        
        for batch_idx, (data, target) in enumerate(train_loader):
            # Forward pass
            logits = model(data)
            loss = criterion(logits, target)
            
            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            if batch_idx % 100 == 0:
                print(f"Epoch {epoch}, Batch {batch_idx}, Loss: {loss.item():.4f}")
    
    # 4. Save model
    torch.save(model.state_dict(), f"models/experiment_{config['name']}.pt")
    
    return model
```

**What happens here:**
- Loads training data using data loader
- Initializes model architecture
- Runs training loop (forward/backward passes)
- Saves trained model weights

---

## 📊 Cell 8: Uncertainty Quantification

**File**: `src/metrics/mc_dropout_uq.py`

```python
# CELL 8: MC Dropout Uncertainty Estimation
def estimate_uncertainty(model, data_loader, mc_passes=20):
    """
    Estimate uncertainty using MC Dropout
    """
    model.train()  # Keep dropout active
    
    all_predictions = []
    
    # Multiple forward passes with dropout
    for _ in range(mc_passes):
        predictions = []
        
        with torch.no_grad():
            for data, _ in data_loader:
                logits = model(data)
                probs = torch.softmax(logits, dim=1)
                predictions.append(probs)
        
        all_predictions.append(torch.cat(predictions))
    
    # Stack predictions: [mc_passes, n_samples, n_classes]
    all_predictions = torch.stack(all_predictions)
    
    # Calculate uncertainty metrics
    mean_probs = all_predictions.mean(dim=0)  # Average over MC passes
    
    # Epistemic uncertainty (variance across passes)
    epistemic = all_predictions.var(dim=0).sum(dim=1)
    
    # Aleatoric uncertainty (entropy of mean prediction)
    aleatoric = -(mean_probs * torch.log(mean_probs + 1e-10)).sum(dim=1)
    
    # Total uncertainty
    total = epistemic + aleatoric
    
    return {
        "epistemic": epistemic.numpy(),
        "aleatoric": aleatoric.numpy(),
        "total": total.numpy(),
        "predictions": mean_probs.numpy()
    }
```

**What happens here:**
- Runs model multiple times with dropout enabled
- Collects predictions from each pass
- Calculates epistemic uncertainty (model uncertainty)
- Calculates aleatoric uncertainty (data uncertainty)
- Returns uncertainty scores for each sample

---

## 📈 Cell 9: Signal Calculation

**File**: `src/walaris/notebook_support/signals.py`

```python
# CELL 9: Calculate Uncertainty Signals
def calculate_signals(uncertainty_results, labels):
    """
    Calculate various uncertainty signals
    """
    signals = {}
    
    # 1. Inverse Mass (epistemic signal)
    # Lower probability mass = higher epistemic uncertainty
    max_probs = uncertainty_results["predictions"].max(axis=1)
    signals["inverse_mass"] = 1 - max_probs
    
    # 2. Dominance (epistemic signal)
    # Difference between top 2 predictions
    sorted_probs = np.sort(uncertainty_results["predictions"], axis=1)
    signals["dominance"] = sorted_probs[:, -1] - sorted_probs[:, -2]
    
    # 3. Inverse Logit Magnitude (epistemic signal)
    # Magnitude of logits (before softmax)
    signals["inverse_logit_magnitude"] = 1 / (np.abs(logits).max(axis=1) + 1e-10)
    
    # 4. Inverse Coherence (aleatoric signal)
    # Disagreement across MC dropout passes
    signals["inverse_coherence"] = uncertainty_results["epistemic"]
    
    # 5. Baseline signals
    signals["msp_uncertainty"] = 1 - max_probs  # Maximum Softmax Probability
    signals["predictive_entropy"] = uncertainty_results["aleatoric"]
    
    return signals
```

**What happens here:**
- Takes uncertainty estimation results
- Calculates multiple uncertainty signals
- Each signal targets different uncertainty types
- Returns dictionary of signal values

---

## ✅ Cell 10: Evaluation & Validation

**File**: `src/walaris/notebook_support/signals.py`

```python
# CELL 10: Validate Signals with UDE
def calculate_ude_scores(signals, ground_truth_labels, predicted_labels):
    """
    Calculate Uncertainty Disentanglement Error (UDE)
    """
    # Identify sample types
    under_supported = identify_under_supported_samples(...)
    noisy_labels = identify_noisy_samples(...)
    
    # For each signal, check if it correctly identifies uncertainty sources
    ude_scores = {}
    
    for signal_name, signal_values in signals.items():
        # C1: High signal for under-supported samples
        c1_score = check_condition_c1(signal_values, under_supported)
        
        # C2: High signal for noisy samples
        c2_score = check_condition_c2(signal_values, noisy_labels)
        
        # O1: Low signal for well-supported clean samples
        o1_score = check_condition_o1(signal_values, under_supported, noisy_labels)
        
        # O2: Correct predictions have lower signal
        o2_score = check_condition_o2(signal_values, predicted_labels, ground_truth_labels)
        
        # Calculate UDE (violations of conditions)
        ude = (1 - c1_score) + (1 - c2_score) + (1 - o1_score) + (1 - o2_score)
        
        ude_scores[signal_name] = {
            "ude": ude,
            "c1": c1_score,
            "c2": c2_score,
            "o1": o1_score,
            "o2": o2_score
        }
    
    return ude_scores
```

**What happens here:**
- Validates uncertainty signals
- Checks if signals correctly identify uncertainty sources
- Calculates UDE score (lower is better)
- Returns quality metrics for each signal

---

## 📊 Cell 11: Results Visualization

**File**: `src/walaris/ui_components/signal_diagnostic_viz.py`

```python
# CELL 11: Visualize Results
def plot_signal_diagnostics(signals, ude_scores, sample_groups):
    """
    Create diagnostic plots for signals
    """
    import matplotlib.pyplot as plt
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # Plot 1: Signal distributions by group
    for signal_name, signal_values in signals.items():
        for group_name, group_indices in sample_groups.items():
            axes[0, 0].hist(
                signal_values[group_indices],
                label=f"{signal_name} - {group_name}",
                alpha=0.5
            )
    axes[0, 0].set_title("Signal Distributions")
    axes[0, 0].legend()
    
    # Plot 2: UDE scores
    signal_names = list(ude_scores.keys())
    ude_values = [ude_scores[s]["ude"] for s in signal_names]
    
    axes[0, 1].bar(signal_names, ude_values)
    axes[0, 1].set_title("UDE Scores (Lower is Better)")
    axes[0, 1].set_xlabel("Signal")
    axes[0, 1].set_ylabel("UDE Score")
    
    # Plot 3: ROC curves
    # ... ROC curve plotting code ...
    
    # Plot 4: Confusion matrix
    # ... confusion matrix plotting code ...
    
    plt.tight_layout()
    return fig
```

**What happens here:**
- Creates visualizations of results
- Shows signal distributions
- Displays UDE scores
- Generates ROC curves and confusion matrices
- Returns matplotlib figure for display in Streamlit

---

## 🔄 Complete Flow Summary

```
┌─────────────────────────────────────────────────────────────┐
│ 1. USER INTERACTION (Streamlit)                             │
│    - Select dataset, model, parameters                      │
│    - Click "Launch Experiment"                              │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. UI COMPONENTS                                             │
│    - render_dataset_selection()                             │
│    - build_base_experiment_config()                         │
│    - Collect all user inputs                                │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. API CALL (HTTP POST)                                     │
│    - POST /api/v1/experiments/no-auth                       │
│    - Send experiment config JSON                            │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. BACKEND API (FastAPI)                                    │
│    - Receive config                                         │
│    - Save to database                                       │
│    - Trigger training pipeline                              │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. DATA LOADING                                             │
│    - CIFAR10NDataset loads images                           │
│    - Apply noise if specified                               │
│    - Create train/eval splits                               │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. MODEL TRAINING                                           │
│    - Initialize DINOv2Classifier                            │
│    - Run training loop                                      │
│    - Save model weights                                     │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. UNCERTAINTY ESTIMATION                                   │
│    - MC Dropout (20 passes)                                 │
│    - Calculate epistemic/aleatoric                          │
│    - Generate predictions                                   │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 8. SIGNAL CALCULATION                                       │
│    - inverse_mass, dominance, etc.                          │
│    - Calculate for all samples                              │
│    - Store signal values                                    │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 9. VALIDATION (UDE)                                         │
│    - Check C1, C2, O1, O2 conditions                        │
│    - Calculate UDE scores                                   │
│    - Identify best signals                                  │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 10. VISUALIZATION                                           │
│     - Plot signal distributions                             │
│     - Show UDE scores                                       │
│     - Display in Streamlit                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 File Organization

```
walaris-cen/
├── streamlit_app.py                    # Cell 1: Entry point
├── streamlit_app_progressive.py        # Cell 1: Progressive UI
│
├── ui_components/                      # Cell 2: UI layer
│   ├── experiment_config.py           # Config builders
│   ├── results.py                     # Results display
│   └── signal_diagnostic_viz.py       # Cell 11: Visualizations
│
├── backend/app/                        # Cell 4: API layer
│   ├── main.py                        # FastAPI app
│   └── api/routes/
│       ├── experiments.py             # Experiment endpoints
│       └── datasets.py                # Dataset endpoints
│
├── src/
│   ├── data/                          # Cell 5: Data loading
│   │   └── cifar10n_loader.py        # CIFAR-10N dataset
│   │
│   ├── walaris/classification/        # Cell 6: Models
│   │   └── models.py                  # DINOv2Classifier
│   │
│   ├── metrics/                       # Cell 8: Uncertainty
│   │   └── mc_dropout_uq.py          # MC Dropout
│   │
│   └── walaris/notebook_support/      # Cell 9-10: Analysis
│       └── signals.py                 # Signal calculation & UDE
│
└── scripts/                           # Cell 7: Training
    └── run_fast_uncertainty_classification.py
```

---

## 🎯 Key Takeaways

1. **Streamlit → UI Components → Backend API** - User interaction flow
2. **Backend → Data Loaders → Models** - Training pipeline
3. **Models → Uncertainty → Signals → Validation** - Analysis pipeline
4. **Results → Visualization → Streamlit** - Display results

Each "cell" represents a logical step in the process, similar to Jupyter notebook cells that execute sequentially.