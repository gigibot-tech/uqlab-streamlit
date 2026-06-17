# UQ Benchmarks Package - Implementation Summary

## What We Built

A **new, clean package** (`uq_benchmarks`) that integrates formal uncertainty quantification methods from research with production infrastructure.

### Key Achievement
✅ **Phase 1 Complete**: Package structure and data layer implemented

## Package Structure

```
uqlab-streamlit/uq_benchmarks/
├── __init__.py                 # Package exports and version
├── setup.py                    # Installation configuration
├── README.md                   # Comprehensive documentation
├── datatypes.py                # Core data structures
├── data/
│   ├── __init__.py
│   └── cifar10.py             # CIFAR-10 loader with noise & epistemic manipulation
├── models/                     # TODO: UQ method implementations
│   └── __init__.py
├── benchmarks/                 # TODO: Formal benchmark experiments
│   └── __init__.py
└── utils/                      # TODO: Helper functions
    └── __init__.py
```

## What's Implemented

### 1. Core Data Types (`datatypes.py`)

#### Dataset
```python
@dataclass
class Dataset:
    X_train: np.ndarray          # Training features
    y_train: np.ndarray          # Training labels
    X_test: np.ndarray           # Test features
    y_test: np.ndarray           # Test labels
    is_regression: bool = False  # Task type
    
    # Noise tracking (NEW)
    noise_mask: Optional[np.ndarray] = None      # Boolean mask for noisy labels
    clean_labels: Optional[np.ndarray] = None    # Original clean labels
    noise_rate: float = 0.0                      # Percentage of noise
```

**Why this matters**: 
- Works with both Keras and PyTorch (NumPy arrays)
- Tracks label noise for aleatoric uncertainty experiments
- Simple, clean abstraction

#### UncertaintyResults
```python
@dataclass
class UncertaintyResults:
    accuracies: List[float]
    aleatoric_uncertainties: List[float]
    epistemic_uncertainties: List[float]
    changed_parameter_values: List[float]
    
    def append_values(self, accuracy, aleatoric, epistemic, parameter):
        # Add result point
    
    def to_dict(self):
        # JSON serialization for API
```

**Why this matters**:
- Standard format for benchmark results
- Easy to plot and analyze
- Compatible with existing visualization code

### 2. CIFAR-10 Data Loader (`data/cifar10.py`)

#### Basic Loader
```python
def get_cifar10_dataset(
    test_mode: bool = False,
    noise_rate: float = 0.0,
    seed: int = 42
) -> Dataset:
```

**Features**:
- Loads CIFAR-10 from Keras datasets
- Normalizes to [0, 1]
- Injects label noise at specified rate
- Tracks which labels are noisy
- Test mode for quick experiments

**Example**:
```python
# Standard CIFAR-10
dataset = get_cifar10_dataset()

# With 40% label noise (aleatoric uncertainty)
noisy = get_cifar10_dataset(noise_rate=0.4)

# Quick test (100 samples)
test = get_cifar10_dataset(test_mode=True)
```

#### Epistemic Manipulation Loader
```python
def get_cifar10_with_epistemic_manipulation(
    under_supported_classes: list[int],
    under_train_per_class: int = 50,
    regular_train_per_class: int = 300,
    eval_per_class: int = 100,
    noise_rate: float = 0.0,
    seed: int = 42
) -> Dataset:
```

**Features**:
- Creates class imbalance for epistemic uncertainty
- Some classes have few samples (under-supported)
- Other classes have normal samples
- Balanced test set for fair evaluation
- Can combine with label noise (aleatoric)

**Example**:
```python
# Under-support cats (3) and dogs (5)
dataset = get_cifar10_with_epistemic_manipulation(
    under_supported_classes=[3, 5],
    under_train_per_class=50,      # Only 50 samples for cats/dogs
    regular_train_per_class=300,   # 300 samples for other classes
    eval_per_class=100,            # Balanced test: 100 per class
    noise_rate=0.2,                # Add 20% label noise
    seed=42
)

# Result:
# - Training: 50*2 + 300*8 = 2,500 samples (imbalanced)
# - Test: 100*10 = 1,000 samples (balanced)
# - 20% of training labels are noisy
```

**Why this matters**:
- Directly implements the epistemic/aleatoric manipulation from the research paper
- Matches the current system's approach but with cleaner code
- Enables formal validation of C1/C2 criteria

### 3. Package Configuration (`setup.py`)

```python
install_requires=[
    "numpy>=1.21.0",
    "scikit-learn>=1.0.0",
]

extras_require={
    "keras": ["keras>=3.0.0", "tensorflow>=2.13.0"],
    "torch": ["torch>=2.0.0", "torchvision>=0.15.0"],
    "all": [...],  # Both frameworks
    "dev": [...],  # Development tools
}
```

**Installation**:
```bash
# Basic (NumPy only)
pip install -e uq_benchmarks/

# With Keras (for Gaussian Logits, IT methods)
pip install -e uq_benchmarks/[keras]

# With PyTorch (for DualXDA)
pip install -e uq_benchmarks/[torch]

# Everything
pip install -e uq_benchmarks/[all]
```

## Design Principles Applied

### 1. ✅ Clean Separation
- **New package**, not modifications to existing code
- Can be developed independently
- No risk of breaking production system

### 2. ✅ Framework Agnostic
- NumPy arrays as common format
- Works with both Keras and PyTorch
- Easy conversion to framework-specific formats

### 3. ✅ Research to Production
- Data structures from `uq_disentanglement_comparison`
- Compatible with existing `uq_classification` infrastructure
- Best of both worlds

### 4. ✅ Well Documented
- Comprehensive README
- Docstrings for all functions
- Usage examples
- Clear architecture

## What's Next (Phase 2)

### Immediate Next Steps

1. **UQ Method Interface** (`models/base.py`)
```python
class UQMethod(ABC):
    @abstractmethod
    def train_and_evaluate(self, dataset: Dataset, config: dict) -> UncertaintyResults:
        """Train model and return (accuracy, aleatoric, epistemic)"""
        pass
```

2. **Gaussian Logits Implementation** (`models/gaussian_logits.py`)
   - Copy from `uq_disentanglement_comparison-72CC/disentanglement/models/gaussian_logits_models.py`
   - Adapt to use our `Dataset` format
   - Return `UncertaintyResults`

3. **Information-Theoretic Implementation** (`models/information_theoretic.py`)
   - Copy from `uq_disentanglement_comparison-72CC/disentanglement/models/information_theoretic_models.py`
   - Implement MI = PE - EE decomposition
   - Return `UncertaintyResults`

4. **DualXDA Adapter** (`models/dualxda_adapter.py`)
   - Wrap existing `uq_classification` code
   - Translate between formats
   - Conform to `UQMethod` interface

## Integration Plan

### Backend Integration (Phase 3)
```python
# backend/app/api/routes/benchmarks.py
from uq_benchmarks.data.cifar10 import get_cifar10_dataset
from uq_benchmarks.models.gaussian_logits import GaussianLogitsMethod

@router.post("/experiments/benchmark")
async def run_benchmark(config: BenchmarkConfig):
    # Load data
    dataset = get_cifar10_dataset(noise_rate=config.noise_rate)
    
    # Run UQ method
    method = GaussianLogitsMethod()
    results = method.train_and_evaluate(dataset, config.model_config)
    
    # Store in PostgreSQL
    experiment = UncertaintyExperiment(
        name=config.name,
        uq_method="gaussian_logits",
        aleatoric_auroc=results.aleatoric_uncertainties[-1],
        epistemic_auroc=results.epistemic_uncertainties[-1],
        ...
    )
    session.add(experiment)
    session.commit()
    
    return experiment
```

### Streamlit Integration (Phase 5)
```python
# streamlit_app.py
from uq_benchmarks.data.cifar10 import get_cifar10_with_epistemic_manipulation

st.header("🔬 UQ Benchmark Experiment")

# Dataset configuration
under_classes = st.multiselect("Under-supported classes", range(10), [3, 5])
noise_rate = st.slider("Label noise rate", 0.0, 1.0, 0.2)

# UQ method selection
methods = st.multiselect("UQ Methods", 
    ["Gaussian Logits", "Information-Theoretic", "DualXDA"],
    ["Gaussian Logits"]
)

if st.button("Run Experiment"):
    dataset = get_cifar10_with_epistemic_manipulation(
        under_supported_classes=under_classes,
        noise_rate=noise_rate
    )
    
    for method_name in methods:
        # Run each method
        results = run_method(method_name, dataset)
        st.write(f"{method_name}: Aleatoric={results.aleatoric:.3f}, Epistemic={results.epistemic:.3f}")
```

## Testing Strategy

### Unit Tests
```python
# tests/test_cifar10.py
def test_cifar10_basic_loading():
    dataset = get_cifar10_dataset(test_mode=True)
    assert dataset.X_train.shape[0] == 500
    assert dataset.X_test.shape[0] == 100
    assert dataset.noise_rate == 0.0

def test_cifar10_noise_injection():
    dataset = get_cifar10_dataset(noise_rate=0.4, test_mode=True)
    assert dataset.noise_rate == 0.4
    assert dataset.noise_mask is not None
    assert dataset.noise_mask.sum() / len(dataset.y_train) == pytest.approx(0.4, abs=0.05)

def test_epistemic_manipulation():
    dataset = get_cifar10_with_epistemic_manipulation(
        under_supported_classes=[3, 5],
        under_train_per_class=50,
        regular_train_per_class=300
    )
    # Check class distribution
    for class_idx in range(10):
        count = (dataset.y_train == class_idx).sum()
        if class_idx in [3, 5]:
            assert count == 50
        else:
            assert count == 300
```

## Success Metrics

### Phase 1 (✅ Complete)
- [x] Package structure created
- [x] Core datatypes defined
- [x] CIFAR-10 loader implemented
- [x] Epistemic manipulation implemented
- [x] Documentation complete
- [x] Setup.py configured

### Phase 2 (🚧 Next)
- [ ] UQ method interface defined
- [ ] Gaussian Logits implemented
- [ ] Information-Theoretic implemented
- [ ] DualXDA adapter created
- [ ] All methods return UncertaintyResults

### Phase 3-8 (📋 Planned)
- [ ] Backend API routes
- [ ] Database schema updates
- [ ] Streamlit UI components
- [ ] Benchmark visualizations
- [ ] Comprehensive testing
- [ ] Performance optimization

## Key Advantages

### vs. Current System (`uq_classification`)
1. **Cleaner code**: Separate package, no legacy baggage
2. **Multiple methods**: Not just DualXDA
3. **Formal benchmarks**: Label noise, dataset size, OOD
4. **Better abstractions**: Dataset format, UncertaintyResults

### vs. Research Package (`uq_disentanglement_comparison`)
1. **Production ready**: FastAPI, PostgreSQL, Streamlit
2. **Better UX**: Web interface, not just scripts
3. **Persistent storage**: Database, not just files
4. **Scalable**: Batch experiments, async execution

### Best of Both Worlds
- Research rigor + Production infrastructure
- Formal methods + User-friendly interface
- Reproducibility + Scalability

## Next Session Plan

1. **Implement UQ Method Interface** (30 min)
   - Define abstract base class
   - Document interface contract
   - Create factory pattern

2. **Port Gaussian Logits** (1 hour)
   - Copy from disentanglement package
   - Adapt to Dataset format
   - Test with CIFAR-10

3. **Port Information-Theoretic** (1 hour)
   - Copy MI/EE/PE implementation
   - Adapt to Dataset format
   - Test with CIFAR-10

4. **Create DualXDA Adapter** (30 min)
   - Wrap existing code
   - Format translation
   - Test compatibility

5. **Integration Testing** (30 min)
   - All 3 methods work
   - Same dataset, different results
   - Results are reasonable

## Questions for User

1. **Priority**: Should we finish all UQ methods first, or integrate one method end-to-end?
2. **DualXDA**: Keep as-is or refactor to match new interface?
3. **Database**: Add new tables now or wait until methods are ready?
4. **UI**: Build new Streamlit pages or extend existing ones?

## Resources

- **Architecture Plan**: `ARCHITECTURE_REWORK_PLAN.md`
- **Package README**: `uq_benchmarks/README.md`
- **Research Paper**: `2408.12175v3.pdf`
- **Original Package**: `uq_disentanglement_comparison-72CC/`

---

**Status**: Phase 1 Complete ✅  
**Next**: Phase 2 - UQ Method Implementations  
**Timeline**: ~3-4 hours for Phase 2  
**Risk**: Low (clean separation, no breaking changes)