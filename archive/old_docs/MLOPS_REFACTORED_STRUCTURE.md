# MLOps Refactored Structure

## 🎯 Current Problem

The current structure mixes concerns and makes it hard to follow the ML pipeline:

```
uqlab-streamlit/
├── src/
│   ├── data/                    # Data loading
│   ├── uqlab/classification/  # Models
│   ├── metrics/                 # Uncertainty
│   └── uqlab/notebook_support/# Analysis
├── scripts/                     # Training scripts
├── backend/                     # API
└── ui_components/               # UI
```

**Issues**:
- ❌ Hard to see the ML pipeline flow
- ❌ Shared code scattered across folders
- ❌ Not clear what depends on what
- ❌ Difficult to reuse components

---

## ✅ Proposed MLOps Structure

Organize by **ML pipeline stages** following MLOps best practices:

```
uqlab-streamlit/
│
├── 📊 1_data/                   # DATA STAGE
│   ├── __init__.py
│   ├── loaders/
│   │   ├── __init__.py
│   │   ├── cifar10n.py         # CIFAR-10N dataset
│   │   └── base.py             # Base dataset class
│   │
│   ├── preprocessing/
│   │   ├── __init__.py
│   │   ├── transforms.py       # Image transforms
│   │   └── augmentation.py     # Data augmentation
│   │
│   └── validation/
│       ├── __init__.py
│       └── data_quality.py     # Data quality checks
│
├── 🧠 2_models/                 # MODEL STAGE
│   ├── __init__.py
│   ├── architectures/
│   │   ├── __init__.py
│   │   ├── dinov2.py           # DINOv2 classifier
│   │   ├── resnet.py           # ResNet classifier
│   │   └── base.py             # Base model class
│   │
│   └── registry/
│       ├── __init__.py
│       └── model_registry.py   # Model versioning
│
├── 🏋️ 3_training/              # TRAINING STAGE
│   ├── __init__.py
│   ├── trainers/
│   │   ├── __init__.py
│   │   ├── standard.py         # Standard training
│   │   └── uncertainty.py      # Uncertainty-aware training
│   │
│   ├── callbacks/
│   │   ├── __init__.py
│   │   ├── checkpointing.py    # Save checkpoints
│   │   └── logging.py          # Training logs
│   │
│   └── config/
│       ├── __init__.py
│       └── training_config.py  # Training configurations
│
├── 📊 4_evaluation/             # EVALUATION STAGE
│   ├── __init__.py
│   ├── uncertainty/
│   │   ├── __init__.py
│   │   ├── mc_dropout.py       # MC Dropout
│   │   ├── ensemble.py         # Ensemble methods
│   │   └── calibration.py      # Calibration
│   │
│   ├── metrics/
│   │   ├── __init__.py
│   │   ├── accuracy.py         # Classification metrics
│   │   ├── uncertainty.py      # Uncertainty metrics
│   │   └── ude.py              # UDE calculation
│   │
│   └── signals/
│       ├── __init__.py
│       ├── epistemic.py        # Epistemic signals
│       ├── aleatoric.py        # Aleatoric signals
│       └── baseline.py         # Baseline signals
│
├── 📈 5_monitoring/             # MONITORING STAGE
│   ├── __init__.py
│   ├── visualization/
│   │   ├── __init__.py
│   │   ├── signal_plots.py     # Signal visualizations
│   │   ├── roc_curves.py       # ROC curves
│   │   └── confusion_matrix.py # Confusion matrices
│   │
│   └── reporting/
│       ├── __init__.py
│       └── experiment_report.py # Generate reports
│
├── 🔄 6_pipeline/               # PIPELINE ORCHESTRATION
│   ├── __init__.py
│   ├── orchestrator.py         # Main pipeline orchestrator
│   ├── stages/
│   │   ├── __init__.py
│   │   ├── data_stage.py       # Data loading stage
│   │   ├── training_stage.py   # Training stage
│   │   ├── eval_stage.py       # Evaluation stage
│   │   └── monitoring_stage.py # Monitoring stage
│   │
│   └── config/
│       ├── __init__.py
│       └── pipeline_config.py  # Pipeline configurations
│
├── 🌐 api/                      # API LAYER
│   ├── __init__.py
│   ├── app.py                  # FastAPI app
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── datasets.py         # Dataset endpoints
│   │   ├── experiments.py      # Experiment endpoints
│   │   └── results.py          # Results endpoints
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py          # Pydantic schemas
│   │
│   └── database/
│       ├── __init__.py
│       ├── models.py           # SQLAlchemy models
│       └── crud.py             # CRUD operations
│
├── 🎨 ui/                       # UI LAYER
│   ├── __init__.py
│   ├── streamlit_app.py        # Main Streamlit app
│   ├── components/
│   │   ├── __init__.py
│   │   ├── dataset_selector.py
│   │   ├── model_config.py
│   │   ├── training_config.py
│   │   └── results_viewer.py
│   │
│   └── utils/
│       ├── __init__.py
│       └── api_client.py       # API client
│
├── 🔧 shared/                   # SHARED UTILITIES
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py         # Global settings
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logging.py          # Logging utilities
│   │   └── file_io.py          # File I/O utilities
│   │
│   └── constants/
│       ├── __init__.py
│       └── constants.py        # Global constants
│
├── 📝 configs/                  # CONFIGURATION FILES
│   ├── datasets/
│   │   └── cifar10n.yaml
│   ├── models/
│   │   ├── dinov2_small.yaml
│   │   └── resnet18.yaml
│   ├── training/
│   │   └── default.yaml
│   └── experiments/
│       └── example.yaml
│
├── 🧪 tests/                    # TESTS
│   ├── unit/
│   │   ├── test_data.py
│   │   ├── test_models.py
│   │   └── test_evaluation.py
│   └── integration/
│       └── test_pipeline.py
│
└── 📚 docs/                     # DOCUMENTATION
    ├── api/
    ├── pipeline/
    └── deployment/
```

---

## 🔄 MLOps Pipeline Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1️⃣ DATA STAGE                                               │
│                                                              │
│ 1_data/loaders/cifar10n.py                                  │
│   ↓                                                          │
│ Load CIFAR-10 images + noisy labels                         │
│   ↓                                                          │
│ 1_data/preprocessing/transforms.py                          │
│   ↓                                                          │
│ Apply transforms & augmentation                             │
│   ↓                                                          │
│ 1_data/validation/data_quality.py                           │
│   ↓                                                          │
│ Validate data quality                                       │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 2️⃣ MODEL STAGE                                              │
│                                                              │
│ 2_models/architectures/dinov2.py                            │
│   ↓                                                          │
│ Initialize DINOv2 + classification head                     │
│   ↓                                                          │
│ 2_models/registry/model_registry.py                         │
│   ↓                                                          │
│ Register model version                                      │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 3️⃣ TRAINING STAGE                                           │
│                                                              │
│ 3_training/trainers/standard.py                             │
│   ↓                                                          │
│ Run training loop                                           │
│   ↓                                                          │
│ 3_training/callbacks/checkpointing.py                       │
│   ↓                                                          │
│ Save checkpoints                                            │
│   ↓                                                          │
│ 3_training/callbacks/logging.py                             │
│   ↓                                                          │
│ Log metrics                                                 │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 4️⃣ EVALUATION STAGE                                         │
│                                                              │
│ 4_evaluation/uncertainty/mc_dropout.py                      │
│   ↓                                                          │
│ Estimate uncertainty (20 MC passes)                         │
│   ↓                                                          │
│ 4_evaluation/signals/epistemic.py                           │
│   ↓                                                          │
│ Calculate epistemic signals                                 │
│   ↓                                                          │
│ 4_evaluation/signals/aleatoric.py                           │
│   ↓                                                          │
│ Calculate aleatoric signals                                 │
│   ↓                                                          │
│ 4_evaluation/metrics/ude.py                                 │
│   ↓                                                          │
│ Calculate UDE scores                                        │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 5️⃣ MONITORING STAGE                                         │
│                                                              │
│ 5_monitoring/visualization/signal_plots.py                  │
│   ↓                                                          │
│ Generate signal visualizations                              │
│   ↓                                                          │
│ 5_monitoring/visualization/roc_curves.py                    │
│   ↓                                                          │
│ Generate ROC curves                                         │
│   ↓                                                          │
│ 5_monitoring/reporting/experiment_report.py                 │
│   ↓                                                          │
│ Generate experiment report                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Key Benefits

### 1. Clear Separation of Concerns
```
1_data/      → Only data loading & preprocessing
2_models/    → Only model definitions
3_training/  → Only training logic
4_evaluation/→ Only evaluation & metrics
5_monitoring/→ Only visualization & reporting
```

### 2. Easy to Navigate
```
Need to modify data loading?     → Go to 1_data/
Need to add a new model?          → Go to 2_models/
Need to change training logic?    → Go to 3_training/
Need to add a new metric?         → Go to 4_evaluation/
Need to create a new plot?        → Go to 5_monitoring/
```

### 3. Reusable Components
```python
# All stages are independent and reusable
from uqlab_cen.data.loaders import CIFAR10NLoader
from uqlab_cen.models.architectures import DINOv2Classifier
from uqlab_cen.training.trainers import StandardTrainer
from uqlab_cen.evaluation.uncertainty import MCDropout
from uqlab_cen.monitoring.visualization import plot_signals
```

### 4. Testable
```
tests/
├── unit/
│   ├── test_data.py       → Test data loaders
│   ├── test_models.py     → Test model architectures
│   └── test_evaluation.py → Test metrics
└── integration/
    └── test_pipeline.py   → Test full pipeline
```

---

## 🔄 Pipeline Orchestration

**File**: `6_pipeline/orchestrator.py`

```python
class MLPipeline:
    """
    Orchestrates the full ML pipeline
    """
    def __init__(self, config):
        self.config = config
        
        # Initialize stages
        self.data_stage = DataStage(config.data)
        self.training_stage = TrainingStage(config.training)
        self.eval_stage = EvaluationStage(config.evaluation)
        self.monitoring_stage = MonitoringStage(config.monitoring)
    
    def run(self):
        """Run full pipeline"""
        # Stage 1: Data
        train_data, eval_data = self.data_stage.load()
        
        # Stage 2: Training
        model = self.training_stage.train(train_data)
        
        # Stage 3: Evaluation
        results = self.eval_stage.evaluate(model, eval_data)
        
        # Stage 4: Monitoring
        report = self.monitoring_stage.generate_report(results)
        
        return report
```

---

## 📦 Shared Components

All stages can access shared utilities:

```python
# Shared configuration
from uqlab_cen.shared.config import settings

# Shared logging
from uqlab_cen.shared.utils import get_logger
logger = get_logger(__name__)

# Shared constants
from uqlab_cen.shared.constants import CLASS_NAMES, NOISE_TYPES
```

---

## 🌐 API Integration

**File**: `api/routes/experiments.py`

```python
from uqlab_cen.pipeline.orchestrator import MLPipeline

@router.post("/experiments/no-auth")
async def create_experiment(experiment: ExperimentCreate):
    # Save to database
    db_experiment = save_experiment(experiment)
    
    # Trigger pipeline
    pipeline = MLPipeline(experiment.config)
    
    # Run asynchronously
    background_tasks.add_task(pipeline.run)
    
    return db_experiment
```

---

## 🎨 UI Integration

**File**: `ui/streamlit_app.py`

```python
from uqlab_cen.ui.components import (
    DatasetSelector,
    ModelConfig,
    TrainingConfig,
    ResultsViewer
)
from uqlab_cen.ui.utils import APIClient

# Use components
dataset = DatasetSelector().render()
model = ModelConfig().render()
training = TrainingConfig().render()

# Submit to API
client = APIClient()
experiment = client.create_experiment({
    "dataset": dataset,
    "model": model,
    "training": training
})
```

---

## 🚀 Migration Plan

### Phase 1: Create New Structure (No Breaking Changes)
```bash
# Create new folders
mkdir -p 1_data/loaders
mkdir -p 2_models/architectures
mkdir -p 3_training/trainers
mkdir -p 4_evaluation/uncertainty
mkdir -p 5_monitoring/visualization
mkdir -p 6_pipeline
```

### Phase 2: Move Files (Keep Old Imports Working)
```python
# New location: 1_data/loaders/cifar10n.py
# Old location: src/data/cifar10n_loader.py

# Keep backward compatibility
# src/data/cifar10n_loader.py:
from uqlab_cen.data.loaders.cifar10n import CIFAR10NDataset
__all__ = ['CIFAR10NDataset']
```

### Phase 3: Update Imports Gradually
```python
# Old import (still works)
from src.data.cifar10n_loader import CIFAR10NDataset

# New import (preferred)
from uqlab_cen.data.loaders import CIFAR10NDataset
```

### Phase 4: Remove Old Structure
```bash
# After all imports updated
rm -rf src/data/
rm -rf src/uqlab/
# etc.
```

---

## ✅ Summary

**Current Structure**: Mixed concerns, hard to navigate
**New Structure**: Clear ML pipeline stages, easy to understand

**Benefits**:
- ✅ Clear separation by ML stage
- ✅ Easy to find and modify code
- ✅ Reusable components
- ✅ Testable
- ✅ Follows MLOps best practices
- ✅ Scalable for future features

**Next Steps**:
1. Create new folder structure
2. Move files gradually
3. Update imports
4. Remove old structure