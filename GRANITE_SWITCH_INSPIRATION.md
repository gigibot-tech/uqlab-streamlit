# Granite-Switch Patterns for UQ Classification

## Transferable Concepts from Granite-Switch to UQ Classification

### 1. **Composable Uncertainty Methods** ✨

**Granite-Switch Pattern:**
- Multiple adapter functions (uncertainty, hallucination, factuality) compose into one model
- Each adapter has a specific input/output contract
- Adapters can be swapped, upgraded, or combined independently

**Apply to UQ Classification:**
```python
# Current: Monolithic uncertainty calculation
uncertainty_signals = calculate_all_signals(predictions, labels)

# Inspired: Composable uncertainty estimators
class UncertaintyEstimator(Protocol):
    """Base protocol for uncertainty estimation methods."""
    def estimate(self, predictions: torch.Tensor, **kwargs) -> Dict[str, float]:
        ...

class MCDropoutEstimator(UncertaintyEstimator):
    """MC Dropout uncertainty estimation."""
    def estimate(self, predictions, mc_passes=20):
        return {"epistemic": ..., "predictive": ...}

class EnsembleEstimator(UncertaintyEstimator):
    """Ensemble-based uncertainty."""
    def estimate(self, predictions, ensemble_size=5):
        return {"epistemic": ..., "aleatoric": ...}

class DeepEnsembleEstimator(UncertaintyEstimator):
    """Deep ensemble uncertainty."""
    def estimate(self, predictions, n_models=5):
        return {"epistemic": ..., "total": ...}

# Compose multiple estimators
uncertainty_pipeline = UncertaintyPipeline([
    MCDropoutEstimator(mc_passes=20),
    EnsembleEstimator(ensemble_size=5),
    DeepEnsembleEstimator(n_models=3)
])

results = uncertainty_pipeline.estimate(predictions)
# Returns: {"mc_dropout": {...}, "ensemble": {...}, "deep_ensemble": {...}}
```

**Benefits:**
- ✅ Easy to add new uncertainty methods
- ✅ Compare methods side-by-side
- ✅ Mix and match for different use cases
- ✅ Independent testing and validation

---

### 2. **Structured Output Contracts** 📋

**Granite-Switch Pattern:**
- Each adapter has a defined output schema (score, decision, rewritten text)
- Output enforced at token level by Mellea
- Predictable, type-safe results

**Apply to UQ Classification:**
```python
from pydantic import BaseModel, Field
from typing import Literal

class UncertaintySignals(BaseModel):
    """Structured uncertainty output contract."""
    
    # Epistemic uncertainty
    epistemic_entropy: float = Field(ge=0.0, description="Model uncertainty")
    epistemic_variance: float = Field(ge=0.0, description="Prediction variance")
    
    # Aleatoric uncertainty
    aleatoric_entropy: float = Field(ge=0.0, description="Data uncertainty")
    
    # Predictive uncertainty
    predictive_entropy: float = Field(ge=0.0, description="Total uncertainty")
    
    # Metadata
    method: Literal["mc_dropout", "ensemble", "deep_ensemble"]
    confidence: float = Field(ge=0.0, le=1.0)
    prediction: int
    
    class Config:
        frozen = True  # Immutable like Granite-Switch adapters

# Usage
signals = MCDropoutEstimator().estimate(predictions)
validated_signals = UncertaintySignals(**signals)  # Type-safe!
```

**Benefits:**
- ✅ Type safety and validation
- ✅ Clear API contracts
- ✅ Easy serialization/deserialization
- ✅ Self-documenting code

---

### 3. **Activation Tokens for Method Selection** 🎯

**Granite-Switch Pattern:**
- `<certainty>`, `<requirements>`, `<guardian>` tokens activate specific adapters
- Clean, explicit method selection
- No ambiguity about which function runs

**Apply to UQ Classification:**
```python
class UncertaintyMethod(Enum):
    """Activation tokens for uncertainty methods."""
    MC_DROPOUT = "mc_dropout"
    ENSEMBLE = "ensemble"
    DEEP_ENSEMBLE = "deep_ensemble"
    GAUSSIAN_PROCESS = "gaussian_process"
    EVIDENTIAL = "evidential"

class UncertaintyEstimator:
    def estimate(
        self, 
        predictions: torch.Tensor,
        method: UncertaintyMethod = UncertaintyMethod.MC_DROPOUT,
        **kwargs
    ) -> UncertaintySignals:
        """Estimate uncertainty using specified method."""
        
        if method == UncertaintyMethod.MC_DROPOUT:
            return self._mc_dropout(predictions, **kwargs)
        elif method == UncertaintyMethod.ENSEMBLE:
            return self._ensemble(predictions, **kwargs)
        # ... etc

# Usage - explicit and clear
signals = estimator.estimate(preds, method=UncertaintyMethod.MC_DROPOUT)
```

**Benefits:**
- ✅ Explicit method selection
- ✅ Type-safe enum
- ✅ Easy to extend
- ✅ Clear in logs and configs

---

### 4. **Efficient Caching Strategy** ⚡

**Granite-Switch Pattern:**
- aLoRA shares KV cache across adapters
- 74% cache hit rate vs 29% for separate LoRAs
- Massive speedup for multi-adapter inference

**Apply to UQ Classification:**
```python
class CachedUncertaintyEstimator:
    """Cache intermediate computations for efficiency."""
    
    def __init__(self):
        self._feature_cache = {}
        self._prediction_cache = {}
    
    def estimate(self, images: torch.Tensor, methods: List[UncertaintyMethod]):
        """Estimate uncertainty with shared feature extraction."""
        
        # Extract features once
        cache_key = hash(images.data_ptr())
        if cache_key not in self._feature_cache:
            features = self.model.extract_features(images)
            self._feature_cache[cache_key] = features
        else:
            features = self._feature_cache[cache_key]
        
        # Run multiple uncertainty methods on same features
        results = {}
        for method in methods:
            results[method.value] = self._estimate_from_features(
                features, method
            )
        
        return results

# Usage - extract features once, run multiple methods
estimator = CachedUncertaintyEstimator()
results = estimator.estimate(
    images, 
    methods=[
        UncertaintyMethod.MC_DROPOUT,
        UncertaintyMethod.ENSEMBLE,
        UncertaintyMethod.EVIDENTIAL
    ]
)
# Much faster than running each method separately!
```

**Benefits:**
- ✅ Avoid redundant feature extraction
- ✅ Faster multi-method evaluation
- ✅ Lower memory usage
- ✅ Better throughput

---

### 5. **Adapter Function Catalog** 📚

**Granite-Switch Pattern:**
- Interactive catalog of all adapter functions
- Benchmarks, use cases, and examples
- Easy discovery and comparison

**Apply to UQ Classification:**
```markdown
# UQ Method Catalog

## MC Dropout
**Type:** Epistemic  
**Speed:** ⚡⚡⚡ Fast  
**Accuracy:** ⭐⭐⭐⭐ High  
**Use Case:** General-purpose uncertainty estimation  
**Benchmark:** AUROC 0.85 on CIFAR-10N  

## Deep Ensemble
**Type:** Epistemic + Aleatoric  
**Speed:** ⚡ Slow  
**Accuracy:** ⭐⭐⭐⭐⭐ Very High  
**Use Case:** High-stakes decisions  
**Benchmark:** AUROC 0.92 on CIFAR-10N  

## Evidential Deep Learning
**Type:** Aleatoric  
**Speed:** ⚡⚡⚡⚡ Very Fast  
**Accuracy:** ⭐⭐⭐ Medium  
**Use Case:** Real-time applications  
**Benchmark:** AUROC 0.78 on CIFAR-10N  
```

**Implementation:**
```python
# Create interactive catalog in Streamlit
def render_method_catalog():
    st.title("🔬 Uncertainty Method Catalog")
    
    for method in UncertaintyMethod:
        with st.expander(f"📊 {method.value}"):
            info = METHOD_REGISTRY[method]
            st.metric("AUROC", info["auroc"])
            st.metric("Speed", info["speed"])
            st.code(info["example_code"])
            
            if st.button(f"Use {method.value}"):
                st.session_state.selected_method = method
```

**Benefits:**
- ✅ Easy method discovery
- ✅ Informed decision-making
- ✅ Reproducible benchmarks
- ✅ Better documentation

---

### 6. **Single Checkpoint, Multiple Backends** 🚀

**Granite-Switch Pattern:**
- Same checkpoint works with HuggingFace and vLLM
- No conversion step
- Choose backend based on use case (prototyping vs production)

**Apply to UQ Classification:**
```python
class UnifiedUQModel:
    """Single model checkpoint, multiple inference backends."""
    
    def __init__(self, checkpoint_path: str):
        self.checkpoint_path = checkpoint_path
        self._torch_model = None
        self._onnx_model = None
        self._trt_model = None
    
    def load_torch(self):
        """Load for training/prototyping."""
        if self._torch_model is None:
            self._torch_model = torch.load(self.checkpoint_path)
        return self._torch_model
    
    def load_onnx(self):
        """Load for CPU inference."""
        if self._onnx_model is None:
            self._onnx_model = onnx.load(f"{self.checkpoint_path}.onnx")
        return self._onnx_model
    
    def load_tensorrt(self):
        """Load for GPU production."""
        if self._trt_model is None:
            self._trt_model = trt.load(f"{self.checkpoint_path}.trt")
        return self._trt_model
    
    def estimate(self, images, backend="torch"):
        """Estimate uncertainty with specified backend."""
        if backend == "torch":
            model = self.load_torch()
        elif backend == "onnx":
            model = self.load_onnx()
        elif backend == "tensorrt":
            model = self.load_tensorrt()
        
        return model.forward(images)

# Usage
model = UnifiedUQModel("./checkpoints/resnet_mcdropout.pt")

# Prototyping
results = model.estimate(images, backend="torch")

# Production
results = model.estimate(images, backend="tensorrt")  # 10x faster!
```

**Benefits:**
- ✅ Single source of truth
- ✅ Easy deployment
- ✅ Flexible backend selection
- ✅ No conversion overhead

---

## Recommended Implementation Plan

### Phase 1: Composable Estimators (Week 1)
1. Create `UncertaintyEstimator` protocol
2. Implement `MCDropoutEstimator`, `EnsembleEstimator`
3. Create `UncertaintyPipeline` for composition
4. Add unit tests

### Phase 2: Structured Outputs (Week 2)
1. Define `UncertaintySignals` Pydantic model
2. Update all estimators to return structured outputs
3. Add validation and type checking
4. Update API endpoints

### Phase 3: Method Catalog (Week 3)
1. Create method registry with benchmarks
2. Build interactive Streamlit catalog
3. Add comparison visualizations
4. Document each method

### Phase 4: Caching & Optimization (Week 4)
1. Implement `CachedUncertaintyEstimator`
2. Add feature extraction caching
3. Benchmark performance improvements
4. Optimize hot paths

### Phase 5: Unified Backend (Week 5)
1. Create `UnifiedUQModel` class
2. Add ONNX export
3. Add TensorRT support
4. Benchmark inference speeds

---

## Code Examples to Steal

### 1. Adapter Registry Pattern
```python
# From granite-switch/src/granite_switch/composer/adapter_discovery.py
ADAPTER_REGISTRY = {
    "mc_dropout": {
        "class": MCDropoutEstimator,
        "type": "epistemic",
        "speed": "fast",
        "accuracy": "high"
    },
    "ensemble": {
        "class": EnsembleEstimator,
        "type": "epistemic",
        "speed": "medium",
        "accuracy": "very_high"
    }
}

def get_estimator(name: str) -> UncertaintyEstimator:
    """Get estimator by name."""
    if name not in ADAPTER_REGISTRY:
        raise ValueError(f"Unknown estimator: {name}")
    return ADAPTER_REGISTRY[name]["class"]()
```

### 2. Structured Configuration
```python
# From granite-switch/src/granite_switch/config.py
class UQConfig(BaseModel):
    """Configuration for uncertainty quantification."""
    
    model_type: Literal["resnet18", "resnet50", "dinov2"]
    uncertainty_methods: List[UncertaintyMethod]
    mc_passes: int = 20
    ensemble_size: int = 5
    cache_features: bool = True
    
    class Config:
        frozen = True
```

### 3. Method Invocation Pattern
```python
# From granite-switch tutorials
def estimate_uncertainty(
    images: torch.Tensor,
    method: UncertaintyMethod,
    model: nn.Module,
    **kwargs
) -> UncertaintySignals:
    """Estimate uncertainty using specified method."""
    
    estimator = get_estimator(method.value)
    return estimator.estimate(images, model=model, **kwargs)
```

---

## Summary

**Top 3 Patterns to Implement:**

1. **Composable Estimators** - Most valuable, enables easy experimentation
2. **Structured Outputs** - Improves code quality and API design
3. **Method Catalog** - Better documentation and discoverability

**Quick Wins:**
- Add `UncertaintyMethod` enum today
- Create `UncertaintySignals` Pydantic model this week
- Build method catalog in Streamlit next week

**Long-term:**
- Implement caching for multi-method evaluation
- Add unified backend support (ONNX, TensorRT)
- Create comprehensive benchmarking suite