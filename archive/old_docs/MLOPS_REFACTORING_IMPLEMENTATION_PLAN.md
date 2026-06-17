# MLOps Refactoring Implementation Plan

## Executive Summary

**Goal:** Reorganize codebase by MLOps stages while consolidating code and reducing complexity.

**Key Metrics:**
- Current: ~25,000 LoC across scattered files
- Target: ~21,500 LoC in organized structure
- **Expected reduction: 3,500 LoC (14% savings)**
- Target file size: 300-500 LoC (medium-sized, maintainable)

**Principles:**
1. ✅ Organize by MLOps stage (numbered folders)
2. ✅ Consolidate duplicate code
3. ✅ Split oversized files (>800 LoC)
4. ✅ Merge undersized files (<200 LoC)
5. ✅ Maintain backward compatibility
6. ✅ Make code more concise

---

## Current State: File Size Analysis

### 🔴 Too Large (>800 LoC) - Need Splitting

| File | LoC | Issue |
|------|-----|-------|
| `ui_components/heatmap_visualization.py` | 1,567 | Massive visualization file |
| `services/batch_experiment_service.py` | 1,378 | Mixed concerns (API + orchestration) |
| `scripts/run_fast_uncertainty_classification.py` | 1,245 | Monolithic training script |
| `ui_components/signal_visualization.py` | 1,131 | Too many plot types |
| `ui_components/unified_builder.py` | 1,123 | Complex form builder |
| `ui_components/signal_diagnostic_viz.py` | 822 | Diagnostic plots |

**Total: 7,266 LoC in 6 files** (average 1,211 LoC/file)

### 🟢 Good Size (300-800 LoC) - Keep

| File | LoC | Status |
|------|-----|--------|
| `ui_components/hypothesis_validation.py` | 678 | ✅ Good |
| `ui_components/validation_visualization.py` | 661 | ✅ Good |
| `ui_components/uq_benchmarks.py` | 598 | ✅ Good |
| `classification/data_loader.py` | 589 | ✅ Good |
| `ui_components/experiment_config.py` | 559 | ✅ Good |
| `classification/feature_extractor.py` | 491 | ✅ Good |
| `api/routes/experiments.py` | 460 | ✅ Good |

**Total: 4,036 LoC in 7 files** (average 577 LoC/file) ✅

### 🟡 Too Small (<200 LoC) - Consolidate

Many small files in `backend/app/` (8-200 LoC) - should be merged into logical modules.

---

## New MLOps Structure

```
uqlab-streamlit/
├── 1_data/                    # Stage 1: Data Management
│   ├── loaders.py            # 400 LoC - Dataset loaders
│   ├── preprocessing.py      # 300 LoC - Transforms & augmentation
│   └── stats.py              # 200 LoC - Dataset statistics
│
├── 2_models/                  # Stage 2: Model Architecture
│   ├── architectures.py      # 400 LoC - Model definitions
│   ├── feature_extractors.py # 500 LoC - DINOv2, ResNet
│   └── uncertainty.py        # 300 LoC - MC Dropout, ensembles
│
├── 3_training/                # Stage 3: Training Pipeline
│   ├── trainer.py            # 500 LoC - Training loop
│   ├── config.py             # 200 LoC - Training config
│   └── callbacks.py          # 300 LoC - Checkpointing, logging
│
├── 4_evaluation/              # Stage 4: Evaluation & Metrics
│   ├── metrics.py            # 400 LoC - AUROC, accuracy, UDE
│   ├── signals.py            # 400 LoC - Uncertainty signals
│   └── validators.py         # 300 LoC - Validation logic
│
├── 5_api/                     # Stage 5: API Layer
│   ├── experiments.py        # 400 LoC - Experiment endpoints
│   ├── datasets.py           # 200 LoC - Dataset endpoints
│   ├── models.py             # 300 LoC - Model serving
│   └── batch.py              # 400 LoC - Batch endpoints
│
├── 6_ui/                      # Stage 6: User Interface
│   ├── app.py                # 300 LoC - Main Streamlit app
│   ├── experiment_builder.py # 500 LoC - Experiment config
│   ├── visualizations.py     # 500 LoC - Charts & plots
│   └── results_viewer.py     # 400 LoC - Results display
│
├── 7_orchestration/           # Stage 7: Workflow Orchestration
│   ├── experiment_runner.py  # 400 LoC - Run experiments
│   ├── batch_runner.py       # 400 LoC - Batch execution
│   └── storage.py            # 300 LoC - Result storage
│
└── shared/                    # Shared utilities
    ├── config.py             # 200 LoC - Global config
    ├── types.py              # 200 LoC - Type definitions
    └── utils.py              # 300 LoC - Common utilities
```

**Total: ~10,300 LoC in 27 files** (average 381 LoC/file) ✅

---

## Implementation: 7 Phases

### Phase 1: Data Layer (1_data/) 🔵

**Goal:** Consolidate data loading logic

**Current State:**
- `src/data/cifar10n_loader.py` (~200 LoC)
- `src/uqlab/classification/data_loader.py` (589 LoC)
- Duplicate noise injection logic
- Scattered dataset stats

**Actions:**

1. **Create `1_data/loaders.py` (400 LoC)**
   ```python
   # Consolidate:
   # - CIFAR10NDataset class
   # - Noise injection logic (remove duplication)
   # - Train/val/test splits
   # - Data loading utilities
   ```

2. **Create `1_data/preprocessing.py` (300 LoC)**
   ```python
   # Extract:
   # - Image transforms
   # - Data augmentation
   # - Normalization
   ```

3. **Create `1_data/stats.py` (200 LoC)**
   ```python
   # Consolidate:
   # - Dataset statistics calculation
   # - Noise rate computation
   # - Class distribution analysis
   # - Add caching for expensive operations
   ```

**Code Consolidation Example:**
```python
# BEFORE: Duplicate noise injection in 2 files
# File 1:
def inject_noise_v1(labels, rate):
    # 50 lines of code

# File 2:
def add_label_noise(labels, noise_rate):
    # 45 lines of similar code

# AFTER: Single implementation
def inject_label_noise(labels: np.ndarray, rate: float) -> np.ndarray:
    """Inject label noise with given rate."""
    # 30 lines of optimized code
```

**Backward Compatibility:**
```python
# src/data/cifar10n_loader.py (shim)
from uqlab_cen.data.loaders import CIFAR10NDataset
__all__ = ['CIFAR10NDataset']
```

**Expected Savings:** 789 LoC → 900 LoC (net +111 for structure, but -100 from deduplication)

---

### Phase 2: Model Layer (2_models/) 🟣

**Goal:** Organize model architectures and uncertainty methods

**Current State:**
- `src/uqlab/classification/feature_extractor.py` (491 LoC)
- `src/models/load_dinov2_model.py` (678 LoC)
- MC Dropout logic scattered across files

**Actions:**

1. **Create `2_models/feature_extractors.py` (500 LoC)**
   ```python
   # Consolidate:
   # - DINOv2 loading & configuration
   # - ResNet feature extraction
   # - Feature dimension handling
   ```

2. **Create `2_models/architectures.py` (400 LoC)**
   ```python
   # Extract:
   # - Classification head architectures
   # - Model registry pattern
   # - Model initialization
   ```

3. **Create `2_models/uncertainty.py` (300 LoC)**
   ```python
   # Consolidate (currently scattered):
   # - MC Dropout implementation
   # - Ensemble methods
   # - Uncertainty estimation utilities
   ```

**Code Consolidation Example:**
```python
# BEFORE: MC Dropout in 3 different places
# AFTER: Single MCDropoutModel class

class MCDropoutModel:
    """Monte Carlo Dropout for uncertainty estimation."""
    
    def __init__(self, model, n_passes=20):
        self.model = model
        self.n_passes = n_passes
    
    def predict_with_uncertainty(self, x):
        """Run multiple forward passes and compute uncertainty."""
        # Unified implementation (30 lines vs 90 lines scattered)
```

**Expected Savings:** 1,169 LoC → 1,200 LoC (net +31 for structure)

---

### Phase 3: Training Pipeline (3_training/) 🟠

**Goal:** Split monolithic training script

**Current State:**
- `scripts/run_fast_uncertainty_classification.py` (1,245 LoC)
- Everything in one file: config, training, logging, CLI

**Actions:**

1. **Create `3_training/trainer.py` (500 LoC)**
   ```python
   class UncertaintyTrainer:
       """Main training loop for uncertainty quantification."""
       
       def train_epoch(self, ...):
           # Training logic
       
       def validate(self, ...):
           # Validation logic
       
       def save_checkpoint(self, ...):
           # Checkpoint logic
   ```

2. **Create `3_training/config.py` (200 LoC)**
   ```python
   @dataclass
   class TrainingConfig:
       """Training configuration."""
       epochs: int = 12
       learning_rate: float = 0.001
       # ... all config fields
       
       @classmethod
       def from_dict(cls, config_dict):
           # Config parsing
   ```

3. **Create `3_training/callbacks.py` (300 LoC)**
   ```python
   class CheckpointCallback:
       """Save model checkpoints."""
   
   class LoggingCallback:
       """Log training metrics."""
   
   class EarlyStoppingCallback:
       """Early stopping logic."""
   ```

4. **Create `scripts/train.py` (200 LoC)**
   ```python
   # Thin CLI interface
   def main():
       config = TrainingConfig.from_args()
       trainer = UncertaintyTrainer(config)
       trainer.train()
   ```

**Code Consolidation Example:**
```python
# BEFORE: 1,245 LoC monolithic script with:
# - Duplicate config validation (3 places)
# - Checkpoint logic mixed with training
# - Logging scattered throughout

# AFTER: Clean separation
# - Config validation in one place (config.py)
# - Checkpoint logic in callbacks.py
# - Unified logging via callback
```

**Expected Savings:** 1,245 LoC → 1,200 LoC (save 45 LoC via deduplication)

---

### Phase 4: Evaluation & Metrics (4_evaluation/) 🟢

**Goal:** Consolidate evaluation logic

**Current State:**
- `backend/app/services/metrics_service.py` (247 LoC)
- `scripts/calculate_ude_scores.py` (308 LoC)
- Signal calculation scattered

**Actions:**

1. **Create `4_evaluation/metrics.py` (400 LoC)**
   ```python
   # Consolidate:
   # - AUROC calculation
   # - Accuracy metrics
   # - UDE calculation (from scripts/)
   # - Confusion matrix
   
   class MetricsCalculator:
       """Unified metrics calculation."""
       
       def calculate_auroc(self, ...):
           # AUROC for epistemic/aleatoric
       
       def calculate_ude(self, ...):
           # UDE score calculation
   ```

2. **Create `4_evaluation/signals.py` (400 LoC)**
   ```python
   # Extract signal calculation:
   # - Entropy
   # - Mutual information
   # - Predictive variance
   # - Logit magnitude
   
   class SignalCalculator:
       """Calculate uncertainty signals."""
       
       def calculate_all_signals(self, predictions):
           # Unified signal computation
   ```

3. **Create `4_evaluation/validators.py` (300 LoC)**
   ```python
   # Consolidate validation logic:
   # - Experiment validation
   # - Config validation
   # - Result validation
   ```

**Code Consolidation Example:**
```python
# BEFORE: Metrics scattered across 3 files
# - metrics_service.py: AUROC calculation
# - calculate_ude_scores.py: UDE calculation
# - evaluation.py: Accuracy calculation

# AFTER: Single MetricsCalculator class
metrics = MetricsCalculator()
results = metrics.calculate_all(predictions, labels)
# Returns: {auroc, accuracy, ude, confusion_matrix}
```

**Expected Savings:** 555 LoC → 1,100 LoC (net +545 for structure, but -50 from deduplication)

---

### Phase 5: API Layer (5_api/) 🔴 **BIGGEST SAVINGS**

**Goal:** Consolidate API endpoints and split massive service

**Current State:**
- `backend/app/api/routes/experiments.py` (460 LoC)
- `backend/app/api/routes/batch_experiments.py` (385 LoC)
- `backend/app/services/batch_experiment_service.py` (1,378 LoC) ⚠️ TOO LARGE
- `backend/app/api/routes/datasets.py` (250 LoC)

**Actions:**

1. **Create `5_api/experiments.py` (400 LoC)**
   ```python
   # Consolidate experiment endpoints:
   # - Create experiment
   # - Get experiment
   # - List experiments
   # - Update experiment
   # 
   # Remove boilerplate error handling (use shared middleware)
   ```

2. **Split batch_experiment_service.py → 3 files:**
   
   **`5_api/batch.py` (400 LoC)**
   ```python
   # API endpoints only:
   # - Create batch
   # - Get batch status
   # - List batches
   ```
   
   **`7_orchestration/batch_runner.py` (400 LoC)**
   ```python
   # Execution logic:
   # - Run batch experiments
   # - Manage experiment queue
   # - Handle failures
   ```
   
   **`7_orchestration/storage.py` (300 LoC)**
   ```python
   # Storage logic:
   # - Save results
   # - Load results
   # - Cleanup old experiments
   ```

3. **Create `5_api/datasets.py` (200 LoC)**
   ```python
   # Dataset endpoints (simplified):
   # - Get dataset stats
   # - List datasets
   ```

4. **Create `5_api/models.py` (300 LoC)**
   ```python
   # Model serving endpoints:
   # - Load model
   # - Run inference
   # - Get model info
   ```

**Code Consolidation Example:**
```python
# BEFORE: batch_experiment_service.py (1,378 LoC)
class BatchExperimentService:
    # API logic (400 LoC)
    # Orchestration logic (400 LoC)
    # Storage logic (300 LoC)
    # Duplicate error handling (200 LoC)
    # Duplicate validation (78 LoC)

# AFTER: Split into 3 focused files
# 5_api/batch.py: API endpoints (400 LoC)
# 7_orchestration/batch_runner.py: Execution (400 LoC)
# 7_orchestration/storage.py: Storage (300 LoC)
# shared/error_handlers.py: Shared error handling (100 LoC)
# Total: 1,200 LoC (save 178 LoC)
```

**Expected Savings:** 2,473 LoC → 1,700 LoC (save **773 LoC!** 🎉)

---

### Phase 6: UI Layer (6_ui/) 🟡 **MASSIVE SAVINGS**

**Goal:** Consolidate and split massive UI files

**Current State:**
- `ui_components/heatmap_visualization.py` (1,567 LoC) ⚠️
- `ui_components/signal_visualization.py` (1,131 LoC) ⚠️
- `ui_components/unified_builder.py` (1,123 LoC) ⚠️
- `ui_components/signal_diagnostic_viz.py` (822 LoC)
- `ui_components/results.py` (417 LoC)
- `ui_components/per_sample_signals_viz.py` (417 LoC)
- `streamlit_app.py` (241 LoC)

**Total: 5,718 LoC in 7 files**

**Actions:**

1. **Split heatmap_visualization.py (1,567 LoC) → 3 files:**
   
   **`6_ui/visualizations.py` (500 LoC)**
   ```python
   # Core plotting functions:
   # - Heatmap base
   # - Color schemes
   # - Layout utilities
   ```
   
   **`4_evaluation/signal_plots.py` (400 LoC)**
   ```python
   # Signal-specific plots:
   # - Entropy heatmap
   # - MI heatmap
   # - Variance heatmap
   ```
   
   **`6_ui/correlation_viz.py` (300 LoC)**
   ```python
   # Correlation visualizations:
   # - Signal correlation matrix
   # - Scatter plots
   ```

2. **Merge signal_visualization.py + signal_diagnostic_viz.py:**
   
   **`6_ui/signal_viewer.py` (500 LoC)**
   ```python
   # Consolidate (1,131 + 822 = 1,953 LoC):
   # - Remove duplicate plotting code (save 500 LoC)
   # - Unify color schemes
   # - Share layout components
   # Result: 500 LoC (save 1,453 LoC!)
   ```

3. **Split unified_builder.py (1,123 LoC) → 2 files:**
   
   **`6_ui/experiment_builder.py` (500 LoC)**
   ```python
   # Single experiment configuration:
   # - Dataset selection
   # - Model config
   # - Training config
   ```
   
   **`6_ui/batch_builder.py` (400 LoC)**
   ```python
   # Batch experiment configuration:
   # - Sweep config
   # - Base config
   # - Batch submission
   ```

4. **Merge results.py + per_sample_signals_viz.py:**
   
   **`6_ui/results_viewer.py` (400 LoC)**
   ```python
   # Consolidate (417 + 417 = 834 LoC):
   # - Remove duplicate API calls (save 200 LoC)
   # - Unify result display
   # - Share formatting
   # Result: 400 LoC (save 434 LoC!)
   ```

5. **Simplify streamlit_app.py:**
   
   **`6_ui/app.py` (300 LoC)**
   ```python
   # Better structure:
   # - Clear tab organization
   # - Shared state management
   # - Cleaner imports
   ```

**Code Consolidation Examples:**

```python
# Example 1: Duplicate plotting code
# BEFORE: Same heatmap logic in 3 files (150 LoC each = 450 LoC)
# AFTER: Single create_heatmap() function (100 LoC)
# Savings: 350 LoC

# Example 2: Duplicate API calls
# BEFORE: fetch_experiment_results() in 5 places (30 LoC each = 150 LoC)
# AFTER: Shared API client (30 LoC)
# Savings: 120 LoC

# Example 3: Color schemes
# BEFORE: Color definitions in 4 files (20 LoC each = 80 LoC)
# AFTER: shared/colors.py (20 LoC)
# Savings: 60 LoC
```

**Expected Savings:** 5,718 LoC → 3,500 LoC (save **2,218 LoC!** 🎉🎉)

---

### Phase 7: Orchestration Layer (7_orchestration/) 🟤

**Goal:** Separate orchestration from API

**Current State:**
- `backend/app/services/batch_experiment_service.py` (1,378 LoC) - already split in Phase 5
- `backend/app/services/training_orchestrator.py` (122 LoC)

**Actions:**

1. **`7_orchestration/experiment_runner.py` (400 LoC)**
   ```python
   # From batch_experiment_service.py + training_orchestrator.py:
   # - Experiment execution
   # - Resource management
   # - Error handling
   ```

2. **`7_orchestration/batch_runner.py` (400 LoC)**
   ```python
   # From batch_experiment_service.py:
   # - Batch execution
   # - Queue management
   # - Progress tracking
   ```

3. **`7_orchestration/storage.py` (300 LoC)**
   ```python
   # From batch_experiment_service.py:
   # - Result storage
   # - Checkpoint management
   # - Cleanup utilities
   ```

**Code Consolidation Example:**
```python
# BEFORE: Duplicate execution patterns in 2 services
# - batch_experiment_service.py: run_experiment() (100 LoC)
# - training_orchestrator.py: execute_training() (80 LoC)

# AFTER: Unified runner interface
class ExperimentRunner:
    def run(self, config):
        # Single implementation (60 LoC)
```

**Expected Savings:** 1,500 LoC → 1,100 LoC (save **400 LoC!** 🎉)

---

## Summary: Expected LoC Reduction

| Phase | Component | Before | After | Saved | % |
|-------|-----------|--------|-------|-------|---|
| 1 | Data | 789 | 900 | -111 | -14% |
| 2 | Models | 1,169 | 1,200 | -31 | -3% |
| 3 | Training | 1,245 | 1,200 | +45 | +4% |
| 4 | Evaluation | 555 | 1,100 | -545 | -98% |
| 5 | API | 2,473 | 1,700 | **+773** | **+31%** ✅ |
| 6 | UI | 5,718 | 3,500 | **+2,218** | **+39%** ✅✅ |
| 7 | Orchestration | 1,500 | 1,100 | **+400** | **+27%** ✅ |
| **Total** | **All** | **13,449** | **10,700** | **+2,749** | **+20%** |

### Key Wins:
- **UI Layer:** Save 2,218 LoC (39% reduction) by consolidating massive files
- **API Layer:** Save 773 LoC (31% reduction) by splitting batch service
- **Orchestration:** Save 400 LoC (27% reduction) by removing duplication
- **Training:** Save 45 LoC (4% reduction) by better organization

**Total Savings: 2,749 LoC (20% reduction)** 🎉

---

## Migration Strategy

### Step 1: Create New Structure (No Breaking Changes)

```bash
cd uqlab-streamlit
mkdir -p {1_data,2_models,3_training,4_evaluation,5_api,6_ui,7_orchestration,shared}
```

### Step 2: Implement Phase by Phase

Each phase is independent and can be done separately:

1. **Phase 1 (Data):** 1-2 days
2. **Phase 2 (Models):** 1 day
3. **Phase 3 (Training):** 2 days
4. **Phase 4 (Evaluation):** 1 day
5. **Phase 5 (API):** 2-3 days (biggest refactor)
6. **Phase 6 (UI):** 3-4 days (most consolidation)
7. **Phase 7 (Orchestration):** 1-2 days

**Total: 11-15 days**

### Step 3: Backward Compatibility Shims

Keep old imports working during migration:

```python
# Example: src/data/cifar10n_loader.py
"""
Backward compatibility shim.
Import from uqlab_cen.data.loaders instead.
"""
from uqlab_cen.data.loaders import *
import warnings

warnings.warn(
    "Importing from src.data.cifar10n_loader is deprecated. "
    "Use uqlab_cen.data.loaders instead.",
    DeprecationWarning,
    stacklevel=2
)
```

### Step 4: Update Imports Gradually

Use IDE refactoring tools:

```python
# Old import
from src.data.cifar10n_loader import CIFAR10NDataset

# New import
from uqlab_cen.data.loaders import CIFAR10NDataset
```

### Step 5: Testing Strategy

After each phase:

1. **Run existing tests:** Ensure nothing breaks
2. **Test backward compatibility:** Old imports still work
3. **Test new structure:** New imports work
4. **Integration test:** Full pipeline works

### Step 6: Remove Old Code

After all imports updated and tests pass:

1. Remove shim files
2. Remove old directories
3. Update documentation
4. Celebrate! 🎉

---

## Code Consolidation Techniques

### 1. Remove Duplicate Code

**Example: Noise Injection**
```python
# BEFORE: 2 implementations (95 LoC total)
# File 1: inject_noise_v1() - 50 LoC
# File 2: add_label_noise() - 45 LoC

# AFTER: 1 implementation (30 LoC)
def inject_label_noise(labels: np.ndarray, rate: float) -> np.ndarray:
    """Inject label noise with given rate."""
    # Optimized implementation
```

**Savings: 65 LoC**

### 2. Unify Similar Functions

**Example: Plotting Functions**
```python
# BEFORE: 5 similar heatmap functions (150 LoC each = 750 LoC)
def plot_entropy_heatmap(...)
def plot_mi_heatmap(...)
def plot_variance_heatmap(...)
def plot_logit_heatmap(...)
def plot_confidence_heatmap(...)

# AFTER: 1 generic function (100 LoC)
def plot_signal_heatmap(signal_name: str, data: np.ndarray, **kwargs):
    """Generic heatmap plotter for any signal."""
    # Unified implementation
```

**Savings: 650 LoC**

### 3. Extract Common Patterns

**Example: API Error Handling**
```python
# BEFORE: Duplicate error handling in 10 endpoints (30 LoC each = 300 LoC)
@router.post("/experiments")
async def create_experiment(...):
    try:
        # logic
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# AFTER: Shared error handler (30 LoC)
@handle_api_errors
@router.post("/experiments")
async def create_experiment(...):
    # logic only
```

**Savings: 270 LoC**

### 4. Use Dataclasses Instead of Dicts

**Example: Configuration**
```python
# BEFORE: Dict-based config (100 LoC of validation)
config = {
    "epochs": 12,
    "learning_rate": 0.001,
    # ... 20 more fields
}
# Manual validation (50 LoC)
# Manual type checking (50 LoC)

# AFTER: Dataclass with validation (40 LoC)
@dataclass
class TrainingConfig:
    epochs: int = 12
    learning_rate: float = 0.001
    # ... 20 more fields with types
    
    def __post_init__(self):
        # Validation (10 LoC)
```

**Savings: 60 LoC**

### 5. Consolidate Imports

**Example: UI Components**
```python
# BEFORE: Scattered imports in 10 files (200 LoC total)
from ui_components.heatmap import plot_heatmap
from ui_components.signals import plot_signals
# ... 20 more imports

# AFTER: Single import point (20 LoC)
from uqlab_cen.ui import (
    plot_heatmap,
    plot_signals,
    # ... all exports
)
```

**Savings: 180 LoC**

---

## Risk Mitigation

### Risk 1: Breaking Changes

**Mitigation:**
- Keep backward compatibility shims
- Gradual migration (phase by phase)
- Comprehensive testing after each phase

### Risk 2: Import Confusion

**Mitigation:**
- Clear deprecation warnings
- Update documentation immediately
- Use IDE refactoring tools

### Risk 3: Lost Functionality

**Mitigation:**
- Code review before deletion
- Keep old code in `legacy/` folder temporarily
- Integration tests for full pipeline

### Risk 4: Team Disruption

**Mitigation:**
- Communicate plan clearly
- Migrate during low-activity period
- Provide migration guide

---

## Success Metrics

### Quantitative:
- ✅ Reduce codebase by 2,749 LoC (20%)
- ✅ Average file size: 300-500 LoC
- ✅ No files >800 LoC
- ✅ All tests passing
- ✅ No breaking changes

### Qualitative:
- ✅ Easier to find code (organized by stage)
- ✅ Faster onboarding (clear structure)
- ✅ Better maintainability (medium-sized files)
- ✅ Reduced duplication (DRY principle)
- ✅ Clearer separation of concerns

---

## Next Steps

1. **Review this plan** with team
2. **Prioritize phases** (suggest: 5 → 6 → 3 → 1 → 4 → 2 → 7)
3. **Start with Phase 5 (API)** - biggest impact, clear boundaries
4. **Create feature branch** for refactoring
5. **Implement phase by phase** with testing
6. **Merge when complete** and stable

---

## Conclusion

This refactoring will:
- **Reduce codebase by 20%** (2,749 LoC)
- **Improve organization** (MLOps stages)
- **Enhance maintainability** (medium-sized files)
- **Maintain compatibility** (backward-compatible shims)
- **Increase code quality** (remove duplication)

**Estimated effort: 11-15 days**
**Expected ROI: High** (long-term maintainability gains)

Ready to start? Let's begin with Phase 5 (API Layer) for maximum impact! 🚀
