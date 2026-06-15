# Final Architecture - Schema Unified & Batching Clarified

## Critical Issues Found & Fixed

### 1. Multiple Conflicting Schemas ❌ → ONE Schema ✅

**Problem**: Found 3 different config schemas:
1. `backend/app/domain/models.py` - Pydantic (PRODUCTION)
2. `src/uqlab/shared/config/schemas.py` - Dataclass (LEGACY)
3. `src/uqlab/6_ui/experiment_builder.py` - Pydantic (OUTDATED)

**Solution**: Use ONLY `backend/app/domain/models.py` (TrainingConfig)

### 2. Wrong Defaults ❌ → Correct Defaults ✅

**Your corrections**:
- MC Dropout default: ~~20~~ → **0** (no MC Dropout by default)
- Model default: ~~dinov2_mlp~~ → **resnet** (ResNet baseline by default)

### 3. Batching Concept ✅

**Your insight is correct**: Batching is purely a UI concept!

## The ONE True Schema (backend/app/domain/models.py)

```python
from pydantic import BaseModel, Field

class TrainingConfig(BaseModel):
    """THE ONLY config schema - all others are deprecated"""
    
    # Top-level
    seed: int = 42
    device: str = "auto"
    
    # Data parameters (flat, not nested)
    noise_type: str = "worse_label"
    aleatoric_noise_percentage: float = 0.0  # Default: no custom noise
    under_supported_classes: str = "3,5"
    under_train_per_class: int = 50
    regular_train_per_class: int = 300
    eval_per_group: int = 600
    
    # Model parameters (flat, not nested)
    architecture: str = "resnet18_mcdropout"  # ✅ Default: ResNet
    training_mode: str = "feature_space"
    dinov2_model: str = "small"  # Only used if architecture="dinov2_mlp"
    hidden_dim: int = 256
    dropout: float = 0.2
    use_untrained_resnet: bool = False
    
    # Training parameters (flat, not nested)
    epochs: int = 12
    learning_rate: float = 0.001
    weight_decay: float = 0.0001
    train_batch_size: int = 256
    feature_batch_size: int = 64
    
    # Evaluation parameters (flat, not nested)
    mc_passes: int = 0  # ✅ Default: 0 (no MC Dropout)
    attribution_method: str = "dualxda"
    top_k: int = 10
    
    # Paths
    cifar10n_root: str = "./data/cifar10n"
    feature_cache_dir: str = "./cache/features"
    results_base_dir: str = "./results"
    
    # Properties for grouped access (backward compatibility)
    @property
    def data(self) -> DataConfig:
        return DataConfig(
            noise_type=self.noise_type,
            aleatoric_noise_percentage=self.aleatoric_noise_percentage,
            ...
        )
    
    @property
    def model(self) -> ModelConfig:
        return ModelConfig(
            architecture=self.architecture,
            dinov2_model=self.dinov2_model,
            ...
        )
```

**Key Points**:
1. **Flat structure** - All fields at top level
2. **Properties for grouping** - `config.data`, `config.model` work but are just views
3. **Correct defaults** - ResNet baseline, no MC Dropout
4. **Single source of truth** - No other schemas should be used

## Batching: Purely a UI Concept ✅

### What is a Batch?

**Batch = Multiple configs with one parameter swept**

```python
# Single experiment
config = {
    "under_train_per_class": 50,
    "aleatoric_noise_percentage": 0.0,
    ...
}

# Batch = 5 configs (sweeping noise)
batch = [
    {..."aleatoric_noise_percentage": 0.0...},   # Config 1
    {..."aleatoric_noise_percentage": 25.0...},  # Config 2
    {..."aleatoric_noise_percentage": 50.0...},  # Config 3
    {..."aleatoric_noise_percentage": 75.0...},  # Config 4
    {..."aleatoric_noise_percentage": 100.0...}, # Config 5
]
```

### Where Batching Happens

**ONLY in UI layer (6_ui/)** - Backend/scripts don't know about batches!

```
┌─────────────────────────────────────────────────────────┐
│ 6_ui/ (Streamlit)                                       │
│                                                         │
│  User selects: "Sweep aleatoric noise [0, 25, 50, 75, 100]" │
│                                                         │
│  UI generates 5 configs:                                │
│  ├─ config_1 (noise=0)                                  │
│  ├─ config_2 (noise=25)                                 │
│  ├─ config_3 (noise=50)                                 │
│  ├─ config_4 (noise=75)                                 │
│  └─ config_5 (noise=100)                                │
│                                                         │
│  UI submits 5 separate experiments to API               │
└─────────────────────────────────────────────────────────┘
        ↓ ↓ ↓ ↓ ↓ (5 separate API calls)
┌─────────────────────────────────────────────────────────┐
│ 5_api/ (FastAPI Backend)                                │
│                                                         │
│  Receives 5 separate experiment creation requests       │
│  Stores 5 separate experiments in database              │
│  Each experiment is independent                         │
└─────────────────────────────────────────────────────────┘
        ↓ ↓ ↓ ↓ ↓ (5 separate script calls)
┌─────────────────────────────────────────────────────────┐
│ scripts/run_fast_*.py                                   │
│                                                         │
│  Runs 5 times (once per config)                         │
│  Each run is independent                                │
│  No knowledge of "batch" concept                        │
└─────────────────────────────────────────────────────────┘
```

### Batch Management in UI

```python
# 6_ui/batch_builder.py
class BatchBuilder:
    """Builds multiple configs from sweep specification"""
    
    def build_aleatoric_batch(
        self,
        base_config: TrainingConfig,
        noise_values: List[float]
    ) -> List[TrainingConfig]:
        """Generate configs for aleatoric sweep"""
        configs = []
        for noise in noise_values:
            # Copy base config
            config = base_config.model_copy()
            # Modify swept parameter
            config.aleatoric_noise_percentage = noise
            configs.append(config)
        return configs
    
    def build_epistemic_batch(
        self,
        base_config: TrainingConfig,
        size_values: List[int]
    ) -> List[TrainingConfig]:
        """Generate configs for epistemic sweep"""
        configs = []
        for size in size_values:
            config = base_config.model_copy()
            config.under_train_per_class = size
            configs.append(config)
        return configs
```

### Streamlit Batch UI

```python
# streamlit_app_progressive.py
def main():
    st.title("Experiment Builder")
    
    # Step 1-4: Build base config
    base_config = build_base_config()  # Returns TrainingConfig
    
    # Step 5: Batch or Single?
    mode = st.radio("Experiment Mode", ["Single", "Batch Sweep"])
    
    if mode == "Single":
        # Submit one config
        if st.button("Create Experiment"):
            client.create_experiment("exp_1", base_config.model_dump())
    
    else:  # Batch
        # Choose sweep type
        sweep_type = st.selectbox("Sweep Type", [
            "Aleatoric (vary noise)",
            "Epistemic (vary dataset size)"
        ])
        
        if sweep_type == "Aleatoric (vary noise)":
            noise_values = st.multiselect(
                "Noise Values (%)",
                [0, 25, 50, 75, 100],
                default=[0, 25, 50, 75, 100]
            )
            
            if st.button("Create Batch"):
                # Generate configs
                builder = BatchBuilder()
                configs = builder.build_aleatoric_batch(
                    base_config,
                    noise_values
                )
                
                # Submit each config separately
                for i, config in enumerate(configs):
                    exp_name = f"alea_sweep_{noise_values[i]}"
                    client.create_experiment(exp_name, config.model_dump())
                
                st.success(f"Created {len(configs)} experiments!")
```

## Corrected Defaults

### Model Default: ResNet (not DINOv2)

```python
# Streamlit form
def render_model_config():
    st.header("2️⃣ Model Configuration")
    
    architecture = st.selectbox("Architecture", [
        "resnet18_mcdropout",  # ✅ DEFAULT
        "dinov2_mlp",
        "cnn_mcdropout"
    ], index=0)  # ResNet is first = default
    
    if architecture == "dinov2_mlp":
        # Only show DINOv2 options if selected
        dinov2_size = st.selectbox("DINOv2 Size", ["small", "base", "large"])
    
    return TrainingConfig(
        architecture=architecture,
        dinov2_model=dinov2_size if architecture == "dinov2_mlp" else "small",
        ...
    )
```

### MC Dropout Default: 0 (disabled)

```python
# Streamlit form
def render_evaluation_config():
    st.header("4️⃣ Evaluation Configuration")
    
    # ✅ Default is 0 (no MC Dropout)
    mc_passes = st.number_input(
        "MC Dropout Passes",
        min_value=0,  # Allow 0
        max_value=100,
        value=0,  # ✅ DEFAULT: 0
        help="Set to 0 to disable MC Dropout (faster, baseline)"
    )
    
    if mc_passes == 0:
        st.info("💡 MC Dropout disabled - using deterministic inference (baseline)")
    else:
        st.info(f"🎲 MC Dropout enabled - {mc_passes} stochastic forward passes")
    
    return TrainingConfig(
        mc_passes=mc_passes,
        ...
    )
```

## Migration Plan: Deprecate Old Schemas

### Step 1: Mark as Deprecated

```python
# src/uqlab/shared/config/schemas.py
import warnings

@dataclass
class DataConfig:
    """
    DEPRECATED: Use backend.app.domain.models.TrainingConfig instead
    
    This schema is kept for backward compatibility only.
    """
    def __post_init__(self):
        warnings.warn(
            "schemas.DataConfig is deprecated. "
            "Use backend.app.domain.models.TrainingConfig instead.",
            DeprecationWarning,
            stacklevel=2
        )
```

### Step 2: Update All Imports

```python
# OLD (deprecated)
from uqlab.shared.config.schemas import ExperimentConfig

# NEW (correct)
from backend.app.domain.models import TrainingConfig
```

### Step 3: Remove Old Files (after migration)

```bash
# After all code is migrated
rm src/uqlab/shared/config/schemas.py
rm src/uqlab/6_ui/experiment_builder.py  # Has outdated schema
```

## Summary

### ✅ Fixed Issues

1. **ONE Schema**: `backend.app.domain.models.TrainingConfig`
2. **Correct Defaults**: ResNet baseline, MC Dropout=0
3. **Batching Clarified**: UI concept only, generates multiple configs
4. **Flat Structure**: All fields at top level, properties for grouping

### 🎯 Key Insights

1. **Batching = UI sugar** - Backend sees N independent experiments
2. **Scripts are batch-agnostic** - Run once per config, no batch knowledge
3. **UI manages sweep logic** - Generates configs, submits separately
4. **One source of truth** - TrainingConfig is the only schema

### 📋 Action Items

1. ✅ Use `TrainingConfig` everywhere
2. ✅ Set correct defaults (ResNet, MC=0)
3. ✅ Implement batching in UI only
4. ⏳ Deprecate old schemas
5. ⏳ Update all imports
6. ⏳ Remove deprecated files

This architecture is now **clean, consistent, and correct**!