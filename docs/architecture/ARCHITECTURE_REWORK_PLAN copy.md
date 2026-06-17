
# Architecture Rework Plan: Hybrid UQ System (Backward Compatible)

## Executive Summary

**Goal**: Rework the current system to use `uq_disentanglement_comparison` as the foundation while maintaining **100% backward compatibility**.

**Approach**: Hybrid architecture using **Adapter Pattern** and **Additive Changes**:
- **Infrastructure**: Keep all existing FastAPI, PostgreSQL, Streamlit (no breaking changes)
- **Core ML**: Add disentanglement methods alongside existing DualXDA
- **Database**: Only ADD new tables/columns (never ALTER or DROP)
- **API**: Add new endpoints (keep all existing ones)

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

---

## Backward Compatibility Principles

### 1. Database: Additive Only
```sql
-- ✅ GOOD: Add new optional columns with defaults
ALTER TABLE uncertaintyexperiment 
  ADD COLUMN uq_method VARCHAR(50) DEFAULT 'dualxda';

-- ✅ GOOD: Add new tables for new features
CREATE TABLE method_comparison (...);

-- ❌ BAD: Never drop or rename existing columns
-- ALTER TABLE uncertaintyexperiment DROP COLUMN aleatoric_auroc;
```

### 2. API: Extend, Don't Replace
```python
# ✅ GOOD: Keep existing endpoints
POST /api/v1/experiments/no-auth  # Still works exactly as before

# ✅ GOOD: Add new endpoints for new features
POST /api/v1/experiments/multi-method  # New endpoint
POST /api/v1/benchmarks/label-noise    # New endpoint

# ❌ BAD: Never change existing endpoint behavior
# POST /api/v1/experiments/no-auth  # Don't change request/response format
```

### 3. Code: Adapter Pattern
```python
# ✅ GOOD: Wrap existing code with adapters
class DualXDAAdapter(UQMethod):
    """Adapts existing DualXDA code to new interface"""
    def __init__(self):
        self.legacy_evaluator = ExistingDualXDAEvaluator()
    
    def evaluate(self, dataset: Dataset) -> UncertaintyResults:
        # Translate new Dataset format to old format
        old_format = self._to_legacy_format(dataset)
        results = self.legacy_evaluator.run(old_format)
        # Translate old results to new format
        return self._from_legacy_format(results)

# ❌ BAD: Don't rewrite existing working code
# class DualXDAAdapter(UQMethod):
#     def evaluate(self, dataset):
#         # Complete rewrite of DualXDA logic
```

---

## Current State Analysis

### Package A: `uq_classification` (Current Production)
```
✅ KEEP UNCHANGED:
- All existing API endpoints
- All existing database tables and columns
- All existing Streamlit pages
- All DualXDA evaluation code
- All existing experiment configs

➕ ADD NEW:
- Adapter layer for DualXDA
- New UQ method interface
- New benchmark endpoints
- New comparison tables
```

### Package B: `uq_disentanglement_comparison` (Research Foundation)
```
✅ ADOPT AS NEW FEATURES:
- Gaussian Logits as new UQ method option
- Information-Theoretic as new UQ method option
- Benchmark framework as new experiment types
- Additional datasets as new options

🔄 INTEGRATE VIA ADAPTERS:
- Wrap Keras models to work with existing infrastructure
- Translate Dataset formats between packages
- Map results to existing database schema
```

---

## New Architecture Design (Additive)

### 1. Data Layer (Adapter Pattern)

```
backend/app/data/
├── adapters/              # NEW: Translation layer
│   ├── __init__.py
│   ├── dataset_adapter.py      # Translates between formats
│   └── results_adapter.py      # Translates results
├── loaders/               # NEW: Additional loaders
│   ├── __init__.py
│   ├── disentanglement_cifar10.py  # From research package
│   ├── fashion_mnist.py            # New dataset
│   └── blobs.py                    # New dataset
└── legacy/                # KEEP: Existing loaders
    └── cifar10n_loader.py  # Unchanged
```

**Adapter Example**:
```python
# backend/app/data/adapters/dataset_adapter.py
class DatasetAdapter:
    """Translates between legacy and disentanglement Dataset formats"""
    
    @staticmethod
    def to_disentanglement_format(legacy_dataset) -> DisentanglementDataset:
        """Convert legacy PyTorch dataset to disentanglement numpy format"""
        return DisentanglementDataset(
            X_train=legacy_dataset.data.numpy(),
            y_train=legacy_dataset.targets.numpy(),
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