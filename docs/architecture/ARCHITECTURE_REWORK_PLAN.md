# Architecture Rework Plan: Hybrid UQ System

## Executive Summary

**Goal**: Rework the current system to use `uq_disentanglement_comparison` as the foundation while keeping DualXDA signals for comparison.

**Approach**: Hybrid architecture that combines:
- **Infrastructure**: FastAPI backend, PostgreSQL, Streamlit UI (from `uq_classification`)
- **Core ML**: Disentanglement methods and benchmarks (from `uq_disentanglement_comparison`)
- **Comparison**: DualXDA signals alongside Gaussian Logits and IT methods

---

## Current State Analysis

### Package A: `uq_classification` (Current Production)
```
✅ KEEP:
- FastAPI backend with PostgreSQL
- Streamlit UI with experiment management
- Batch experiment infrastructure
- Database schema and migrations
- User authentication
- Results visualization (heatmaps, line plots)

❌ REPLACE:
- PyTorch-only training pipeline
- Custom CIFAR-10N loader (use disentanglement's)
- Single-method evaluation approach

🔄 ENHANCE:
- Add DualXDA as one of multiple UQ methods
- Keep 7-signal structure but as one method option
```

### Package B: `uq_disentanglement_comparison` (Research Foundation)
```
✅ ADOPT:
- Dataset loaders (CIFAR-10, Fashion-MNIST, blobs, etc.)
- Gaussian Logits models (two-head architecture)
- Information-Theoretic models (MI, EE, PE)
- Benchmark framework (label_noise, decreasing_dataset, ood_class)
- UncertaintyResults dataclass structure

🔄 ADAPT:
- Convert Keras models to work with FastAPI
- Integrate benchmarks into Streamlit UI
- Store results in PostgreSQL instead of files
```

---

## New Architecture Design

### 1. Data Layer

```
backend/app/data/
├── loaders/
│   ├── __init__.py
│   ├── cifar10.py          # From disentanglement (Keras datasets)
│   ├── cifar10n.py         # Enhanced with noise tracking
│   ├── fashion_mnist.py    # From disentanglement
│   ├── blobs.py            # From disentanglement
│   └── base.py             # Common Dataset dataclass
├── transforms/
│   ├── noise_injection.py  # Label noise utilities
│   └── augmentation.py     # Data augmentation
└── benchmarks/
    ├── label_noise.py      # From disentanglement
    ├── dataset_size.py     # From disentanglement
    └── ood_detection.py    # From disentanglement
```

**Key Changes**:
- Use `disentanglement.datatypes.Dataset` as base
- Keep CIFAR-10N noise tracking from current system
- Support multiple datasets (not just CIFAR-10)

### 2. Model Layer

```
backend/app/models/
├── uq_methods/
│   ├── __init__.py
│   ├── gaussian_logits.py     # From disentanglement (Keras)
│   ├── information_theoretic.py # From disentanglement (Keras)
│   ├── dualxda.py             # Keep from uq_classification (PyTorch)
│   └── base.py                # Common UQ method interface
├── architectures/
│   ├── keras_backbones.py     # From disentanglement
│   ├── pytorch_backbones.py   # Keep DINOv2 for DualXDA
│   └── ensemble.py            # Deep ensemble support
└── training/
    ├── keras_trainer.py       # For GL and IT methods
    └── pytorch_trainer.py     # For DualXDA method
```

**Key Changes**:
- Support **3 UQ methods**: Gaussian Logits, Information-Theoretic, DualXDA
- Each method returns: `(accuracy, aleatoric_uncertainty, epistemic_uncertainty)`
- Common interface for all methods

### 3. Database Schema Updates

```sql
-- Add new fields to UncertaintyExperiment table
ALTER TABLE uncertaintyexperiment ADD COLUMN uq_method VARCHAR(50) DEFAULT 'dualxda';
ALTER TABLE uncertaintyexperiment ADD COLUMN benchmark_type VARCHAR(50);  -- 'label_noise', 'dataset_size', 'ood_class'
ALTER TABLE uncertaintyexperiment ADD COLUMN dataset_name VARCHAR(100) DEFAULT 'cifar10n';

-- Add new table for method comparison results
CREATE TABLE method_comparison (
    id UUID PRIMARY KEY,
    experiment_id UUID REFERENCES uncertaintyexperiment(id),
    method_name VARCHAR(50),
    aleatoric_auroc FLOAT,
    epistemic_auroc FLOAT,
    accuracy FLOAT,
    aleatoric_mean FLOAT,
    epistemic_mean FLOAT,
    created_at TIMESTAMP
);
```

### 4. API Routes

```
backend/app/api/routes/
├── experiments.py          # Enhanced with UQ method selection
├── benchmarks.py           # NEW: Run benchmark experiments
├── datasets.py             # Enhanced with multiple datasets
├── methods.py              # NEW: List available UQ methods
└── comparisons.py          # NEW: Compare methods side-by-side
```

**New Endpoints**:
```python
POST /api/v1/benchmarks/label-noise
POST /api/v1/benchmarks/dataset-size
POST /api/v1/benchmarks/ood-detection
GET  /api/v1/methods                    # List: gaussian_logits, it, dualxda
POST /api/v1/comparisons/run            # Run all 3 methods on same config
GET  /api/v1/comparisons/{id}/results   # Compare results
```

### 5. Streamlit UI Redesign

```
streamlit_app.py (main entry)
├── Dataset Selection
│   ├── CIFAR-10 / CIFAR-10N
│   ├── Fashion-MNIST
│   ├── Blobs (toy dataset)
│   └── Custom datasets
├── UQ Method Selection
│   ├── ☑️ Gaussian Logits (two-head)
│   ├── ☑️ Information-Theoretic (MI/EE)
│   ├── ☑️ DualXDA (7 signals)
│   └── ☑️ Run All (comparison mode)
├── Experiment Type
│   ├── Single Experiment
│   ├── Benchmark: Label Noise Sweep
│   ├── Benchmark: Dataset Size Sweep
│   └── Benchmark: OOD Detection
└── Results Visualization
    ├── Method Comparison Table
    ├── Benchmark Plots (from disentanglement)
    └── Signal Analysis (for DualXDA)
```

---

## Implementation Phases

### Phase 1: Data Layer Integration (Week 1)
**Goal**: Adopt disentanglement data loaders

**Tasks**:
1. Copy `disentanglement/data/` to `backend/app/data/loaders/`
2. Create adapter for `Dataset` dataclass → PostgreSQL
3. Update CIFAR-10N loader to use disentanglement base
4. Add noise injection utilities
5. Test data loading for all datasets

**Files to Create/Modify**:
- `backend/app/data/loaders/cifar10.py`
- `backend/app/data/loaders/base.py`
- `backend/app/api/routes/datasets.py` (add multi-dataset support)

### Phase 2: Model Integration (Week 2)
**Goal**: Add Gaussian Logits and IT methods

**Tasks**:
1. Copy `disentanglement/models/gaussian_logits_models.py`
2. Copy `disentanglement/models/information_theoretic_models.py`
3. Create common UQ method interface
4. Wrap Keras models for FastAPI execution
5. Keep DualXDA as third method option

**Files to Create**:
- `backend/app/models/uq_methods/base.py`
- `backend/app/models/uq_methods/gaussian_logits.py`
- `backend/app/models/uq_methods/information_theoretic.py`
- `backend/app/models/uq_methods/dualxda.py` (refactor existing)

**Interface Design**:
```python
class UQMethod(ABC):
    @abstractmethod
    def train(self, dataset: Dataset, config: dict) -> Model:
        pass
    
    @abstractmethod
    def evaluate(self, model: Model, dataset: Dataset) -> UncertaintyResults:
        """Returns (accuracy, aleatoric_unc, epistemic_unc)"""
        pass
```

### Phase 3: Benchmark Framework (Week 3)
**Goal**: Integrate benchmark experiments

**Tasks**:
1. Copy `disentanglement/benchmarks/` to `backend/app/benchmarks/`
2. Adapt benchmarks to use FastAPI + PostgreSQL
3. Create API routes for benchmark execution
4. Store benchmark results in database

**Files to Create**:
- `backend/app/benchmarks/label_noise.py`
- `backend/app/benchmarks/dataset_size.py`
- `backend/app/benchmarks/ood_detection.py`
- `backend/app/api/routes/benchmarks.py`

### Phase 4: Database Schema (Week 3)
**Goal**: Update schema for multi-method support

**Tasks**:
1. Create migration for new fields
2. Add `method_comparison` table
3. Update repositories to handle multiple methods
4. Migrate existing experiments

**Files to Create/Modify**:
- `backend/app/alembic/versions/xxx_add_uq_methods.py`
- `backend/app/tables.py`
- `backend/app/repositories/experiment_repository.py`

### Phase 5: Streamlit UI Rework (Week 4)
**Goal**: New UI for method selection and benchmarks

**Tasks**:
1. Add UQ method selector (3 checkboxes)
2. Add benchmark type selector
3. Create method comparison view
4. Integrate disentanglement plotting
5. Keep existing signal visualization for DualXDA

**Files to Create/Modify**:
- `streamlit_app.py` (major refactor)
- `ui_components/method_selector.py` (new)
- `ui_components/benchmark_config.py` (new)
- `ui_components/method_comparison.py` (new)

### Phase 6: Visualization Enhancement (Week 5)
**Goal**: Adopt disentanglement plotting

**Tasks**:
1. Port `disentanglement/benchmarks/plotting.py`
2. Create Streamlit wrappers for matplotlib plots
3. Add method comparison charts
4. Keep existing Plotly visualizations

**Files to Create**:
- `ui_components/benchmark_plots.py`
- `ui_components/method_comparison_plots.py`

### Phase 7: Testing & Validation (Week 6)
**Goal**: Ensure all methods work correctly

**Tasks**:
1. Unit tests for each UQ method
2. Integration tests for benchmarks
3. End-to-end tests for UI workflows
4. Validate against paper results

**Files to Create**:
- `tests/test_gaussian_logits.py`
- `tests/test_information_theoretic.py`
- `tests/test_benchmarks.py`

### Phase 8: Documentation (Week 6)
**Goal**: Document new architecture

**Tasks**:
1. Update README with method descriptions
2. Create method comparison guide
3. Document benchmark usage
4. Migration guide for existing users

---

## Key Design Decisions

### 1. Framework Coexistence
**Decision**: Support both Keras and PyTorch
**Rationale**: 
- Gaussian Logits and IT methods are Keras-based (from research)
- DualXDA is PyTorch-based (existing production code)
- Both can coexist in FastAPI backend

**Implementation**:
```python
# backend/app/models/uq_methods/base.py
class UQMethod(ABC):
    framework: str  # 'keras' or 'pytorch'
    
    @abstractmethod
    def train_and_evaluate(self, dataset, config) -> UncertaintyResults:
        pass
```

### 2. Dataset Abstraction
**Decision**: Use `disentanglement.datatypes.Dataset` as standard
**Rationale**:
- Simple dataclass: `(X_train, y_train, X_test, y_test, is_regression)`
- Works with both Keras and PyTorch
- Easy to serialize for API

**Implementation**:
```python
@dataclass
class Dataset:
    X_train: np.ndarray
    y_train: np.ndarray
    X_test: np.ndarray
    y_test: np.ndarray
    is_regression: bool = False
    noise_mask: np.ndarray | None = None  # NEW: track noisy labels
```

### 3. Results Storage
**Decision**: Store per-method results in database
**Rationale**:
- Enable method comparison queries
- Track which method performed best
- Support benchmark result aggregation

**Schema**:
```sql
-- One experiment can have multiple method results
experiment (id, name, config, ...)
  ├── method_result (method='gaussian_logits', ale_auroc=0.85, epi_auroc=0.72)
  ├── method_result (method='it', ale_auroc=0.83, epi_auroc=0.75)
  └── method_result (method='dualxda', ale_auroc=0.88, epi_auroc=0.70)
```

### 4. Benchmark Integration
**Decision**: Benchmarks as first-class experiment types
**Rationale**:
- Formal validation of C1/C2 criteria
- Reproducible research experiments
- Automated method comparison

**UI Flow**:
```
1. Select Experiment Type: "Benchmark: Label Noise"
2. Select Methods: [✓] Gaussian Logits [✓] IT [✓] DualXDA
3. Configure: noise_range=[0, 0.2, 0.4, 0.6, 0.8, 1.0]
4. Run → Creates 6 experiments × 3 methods = 18 runs
5. View: Comparison plot showing all 3 methods across noise levels
```

---

## Migration Strategy

### For Existing Experiments
1. **Backward Compatibility**: Old experiments remain as `uq_method='dualxda'`
2. **Re-run Option**: UI button to "Re-run with all methods"
3. **Comparison View**: Compare old DualXDA results with new methods

### For Existing Code
1. **Keep**: All DualXDA signal code in `uq_classification/`
2. **Wrap**: Create adapter to make DualXDA conform to `UQMethod` interface
3. **Extend**: Add GL and IT as new method options

---

## Success Criteria

### Technical
- [ ] All 3 UQ methods (GL, IT, DualXDA) run successfully
- [ ] All 3 benchmarks (label noise, dataset size, OOD) work
- [ ] Method comparison produces valid results
- [ ] Existing experiments still accessible

### Research
- [ ] Reproduce disentanglement paper results
- [ ] Validate C1/C2 criteria for all methods
- [ ] Compare DualXDA against formal methods

### User Experience
- [ ] Clear method selection in UI
- [ ] Intuitive benchmark configuration
- [ ] Informative comparison visualizations
- [ ] Smooth migration from old system

---

## Risk Mitigation

### Risk 1: Keras/PyTorch Conflicts
**Mitigation**: 
- Run in separate processes if needed
- Use TensorFlow 2.x with eager execution
- Test memory management carefully

### Risk 2: Performance Degradation
**Mitigation**:
- Profile each method's runtime
- Implement caching for repeated runs
- Consider async execution for long benchmarks

### Risk 3: Breaking Changes
**Mitigation**:
- Feature flag for new architecture
- Parallel deployment (old + new)
- Comprehensive testing before cutover

---

## Next Steps

1. **Review this plan** with stakeholders
2. **Set up development branch**: `feature/hybrid-uq-architecture`
3. **Start Phase 1**: Data layer integration
4. **Weekly check-ins**: Track progress against phases

---

## Appendix: File Structure Comparison

### Before (Current)
```
uqlab-streamlit/
├── backend/
│   └── app/
│       ├── api/routes/experiments.py
│       └── tables.py
├── uq_classification/  # PyTorch only
│   ├── data_loader.py
│   └── evaluation.py
└── streamlit_app.py
```

### After (Hybrid)
```
uqlab-streamlit/
├── backend/
│   └── app/
│       ├── api/routes/
│       │   ├── experiments.py
│       │   ├── benchmarks.py  # NEW
│       │   └── methods.py     # NEW
│       ├── data/loaders/      # NEW (from disentanglement)
│       ├── models/uq_methods/ # NEW (3 methods)
│       ├── benchmarks/        # NEW (from disentanglement)
│       └── tables.py          # UPDATED
├── uq_classification/         # KEEP (DualXDA)
└── streamlit_app.py           # MAJOR REFACTOR
```

---

**Document Version**: 1.0  
**Created**: 2026-05-23  
**Author**: Bob (Planning Mode)  
**Status**: Ready for Review