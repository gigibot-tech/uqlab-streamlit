# Final Implementation Plan - Clean & Readable

## The Problem with Current TrainingConfig

**Current (WRONG)**:
```python
# backend/app/domain/models.py
class TrainingConfig(BaseModel):  # ❌ Misleading name!
    # All fields flat at top level
    noise_type: str = "worse_label"  # Data field
    architecture: str = "resnet"      # Model field
    epochs: int = 12                  # Training field
    mc_passes: int = 0                # Evaluation field
```

**This is confusing because**:
- Name says "Training" but contains ALL config
- Flat structure mixes concerns
- Hard to see which field belongs to which step

## The Correct Structure (NESTED)

```python
# backend/app/domain/models.py
class ExperimentConfig(BaseModel):  # ✅ Correct name!
    """Complete experiment configuration with nested sections"""
    
    # Top-level metadata
    seed: int = 42
    device: str = "auto"
    
    # Nested sections (one per folder)
    data: DataConfig
    model: ModelConfig
    training: TrainingRuntimeConfig
    evaluation: EvaluationConfig
    paths: PathsConfig
```

### Section 1: DataConfig (from 1_data/)

```python
class DataConfig(BaseModel):
    """Dataset loading and sampling - maps to 1_data/ folder"""
    
    noise_type: str = "worse_label"
    aleatoric_noise_percentage: float = 0.0
    under_supported_classes: str = "3,5"
    under_train_per_class: int = 50
    regular_train_per_class: int = 300
    eval_per_group: int = 600
```

### Section 2: ModelConfig (from 2_models/)

```python
class ModelConfig(BaseModel):
    """Model architecture - maps to 2_models/ folder"""
    
    architecture: str = "resnet18_mcdropout"  # ✅ ResNet default
    training_mode: str = "feature_space"
    dinov2_model: str = "small"  # Only if architecture="dinov2_mlp"
    hidden_dim: int = 256
    dropout: float = 0.2
    use_untrained_resnet: bool = False
    checkpoint_path: Optional[str] = None  # Load from checkpoint
```

### Section 3: TrainingRuntimeConfig (from 3_training/)

```python
class TrainingRuntimeConfig(BaseModel):
    """Training hyperparameters - maps to 3_training/ folder"""
    
    epochs: int = 12
    learning_rate: float = 0.001
    weight_decay: float = 0.0001
    train_batch_size: int = 256
    feature_batch_size: int = 64
```

### Section 4: EvaluationConfig (from 4_evaluation/)

```python
class EvaluationConfig(BaseModel):
    """Evaluation and UQ parameters - maps to 4_evaluation/ folder"""
    
    mc_passes: int = 0  # ✅ Default: 0 (no MC Dropout)
    attribution_method: str = "dualxda"
    top_k: int = 10
```

### Section 5: PathsConfig

```python
class PathsConfig(BaseModel):
    """File system paths"""
    
    cifar10n_root: str = "./data/cifar10n"
    feature_cache_dir: str = "./cache/features"
    results_base_dir: str = "./results"
```

## Complete Config Example

```python
config = ExperimentConfig(
    seed=42,
    device="auto",
    
    data=DataConfig(
        noise_type="worse_label",
        aleatoric_noise_percentage=0.0,
        under_supported_classes="3,5",
        under_train_per_class=50,
        regular_train_per_class=300,
        eval_per_group=600
    ),
    
    model=ModelConfig(
        architecture="resnet18_mcdropout",
        training_mode="feature_space",
        dinov2_model="small",
        hidden_dim=256,
        dropout=0.2,
        use_untrained_resnet=False,
        checkpoint_path=None
    ),
    
    training=TrainingRuntimeConfig(
        epochs=12,
        learning_rate=0.001,
        weight_decay=0.0001,
        train_batch_size=256,
        feature_batch_size=64
    ),
    
    evaluation=EvaluationConfig(
        mc_passes=0,  # No MC Dropout by default
        attribution_method="dualxda",
        top_k=10
    ),
    
    paths=PathsConfig(
        cifar10n_root="./data/cifar10n",
        feature_cache_dir="./cache/features",
        results_base_dir="./results"
    )
)
```

## JSON Representation (for API)

```json
{
    "seed": 42,
    "device": "auto",
    
    "data": {
        "noise_type": "worse_label",
        "aleatoric_noise_percentage": 0.0,
        "under_supported_classes": "3,5",
        "under_train_per_class": 50,
        "regular_train_per_class": 300,
        "eval_per_group": 600
    },
    
    "model": {
        "architecture": "resnet18_mcdropout",
        "training_mode": "feature_space",
        "dinov2_model": "small",
        "hidden_dim": 256,
        "dropout": 0.2,
        "use_untrained_resnet": false,
        "checkpoint_path": null
    },
    
    "training": {
        "epochs": 12,
        "learning_rate": 0.001,
        "weight_decay": 0.0001,
        "train_batch_size": 256,
        "feature_batch_size": 64
    },
    
    "evaluation": {
        "mc_passes": 0,
        "attribution_method": "dualxda",
        "top_k": 10
    },
    
    "paths": {
        "cifar10n_root": "./data/cifar10n",
        "feature_cache_dir": "./cache/features",
        "results_base_dir": "./results"
    }
}
```

## Streamlit Implementation

### Main App (streamlit_app_progressive.py)

```python
from backend.app.domain.models import (
    ExperimentConfig,
    DataConfig,
    ModelConfig,
    TrainingRuntimeConfig,
    EvaluationConfig,
    PathsConfig
)

def main():
    st.title("🔬 Uncertainty Quantification Experiment Builder")
    
    # Initialize config with correct structure
    if "config" not in st.session_state:
        st.session_state.config = ExperimentConfig(
            seed=42,
            device="auto",
            data=DataConfig(),
            model=ModelConfig(),
            training=TrainingRuntimeConfig(),
            evaluation=EvaluationConfig(),
            paths=PathsConfig()
        )
    
    # Step 1: Data Configuration
    st.session_state.config.data = render_data_config()
    
    # Step 2: Model Configuration
    st.session_state.config.model = render_model_config()
    
    # Step 3: Training Configuration
    st.session_state.config.training = render_training_config()
    
    # Step 4: Evaluation Configuration
    st.session_state.config.evaluation = render_evaluation_config()
    
    # Step 5: Submit
    if st.button("Submit Experiment"):
        client = ExperimentAPIClient(API_URL)
        exp = client.create_experiment(
            name=f"exp_{timestamp}",
            config=st.session_state.config.model_dump()  # Convert to dict
        )
        st.success(f"Experiment {exp['id']} created!")
```

### Form Components

```python
# 6_ui/data_config_form.py
def render_data_config() -> DataConfig:
    """Step 1: Data Configuration Form"""
    st.header("1️⃣ Data Configuration")
    
    noise_type = st.selectbox("Noise Type", [
        "clean_label", "worse_label", "aggre_label"
    ])
    
    custom_noise = st.slider("Custom Noise %", 0, 100, 0)
    under_classes = st.text_input("Under-supported classes", "3,5")
    under_samples = st.number_input("Samples per under-class", 25, 500, 50)
    regular_samples = st.number_input("Samples per regular class", 100, 1000, 300)
    
    return DataConfig(
        noise_type=noise_type,
        aleatoric_noise_percentage=float(custom_noise),
        under_supported_classes=under_classes,
        under_train_per_class=under_samples,
        regular_train_per_class=regular_samples,
        eval_per_group=600
    )

# 6_ui/model_config_form.py
def render_model_config() -> ModelConfig:
    """Step 2: Model Configuration Form"""
    st.header("2️⃣ Model Configuration")
    
    architecture = st.selectbox("Architecture", [
        "resnet18_mcdropout",  # ✅ Default
        "dinov2_mlp",
        "cnn_mcdropout"
    ], index=0)
    
    if architecture == "dinov2_mlp":
        dinov2_size = st.selectbox("DINOv2 Size", ["small", "base", "large"])
        hidden_dim = st.number_input("Hidden Dimension", 64, 1024, 256)
    else:
        dinov2_size = "small"  # Not used
        hidden_dim = 256
    
    dropout = st.slider("Dropout", 0.0, 0.5, 0.2)
    
    return ModelConfig(
        architecture=architecture,
        dinov2_model=dinov2_size,
        hidden_dim=hidden_dim,
        dropout=dropout,
        use_untrained_resnet=False,
        checkpoint_path=None
    )

# 6_ui/training_config_form.py
def render_training_config() -> TrainingRuntimeConfig:
    """Step 3: Training Configuration Form"""
    st.header("3️⃣ Training Configuration")
    
    epochs = st.number_input("Epochs", 1, 100, 12)
    lr = st.number_input("Learning Rate", 0.0001, 0.1, 0.001, format="%.4f")
    weight_decay = st.number_input("Weight Decay", 0.0, 0.01, 0.0001, format="%.4f")
    batch_size = st.selectbox("Batch Size", [64, 128, 256, 512], index=2)
    
    return TrainingRuntimeConfig(
        epochs=epochs,
        learning_rate=lr,
        weight_decay=weight_decay,
        train_batch_size=batch_size,
        feature_batch_size=64
    )

# 6_ui/evaluation_config_form.py
def render_evaluation_config() -> EvaluationConfig:
    """Step 4: Evaluation Configuration Form"""
    st.header("4️⃣ Evaluation Configuration")
    
    mc_passes = st.number_input(
        "MC Dropout Passes",
        min_value=0,  # ✅ Allow 0
        max_value=100,
        value=0,  # ✅ Default: 0
        help="Set to 0 to disable MC Dropout (baseline)"
    )
    
    if mc_passes == 0:
        st.info("💡 MC Dropout disabled - deterministic inference (baseline)")
    else:
        st.info(f"🎲 MC Dropout enabled - {mc_passes} stochastic passes")
    
    attribution = st.selectbox("Attribution Method", [
        "dualxda", "gradcam", "integrated_gradients"
    ])
    
    top_k = st.number_input("Top-K Signals", 1, 50, 10)
    
    return EvaluationConfig(
        mc_passes=mc_passes,
        attribution_method=attribution,
        top_k=top_k
    )
```

## Usage in run_fast_*.py

```python
# scripts/run_fast_uncertainty_classification.py
from backend.app.domain.models import ExperimentConfig

def main():
    # Load config
    config = ExperimentConfig.model_validate_json(
        Path("config.json").read_text()
    )
    
    # Step 1: Load data (using config.data)
    dataset = CIFAR10NDataset(
        root=config.paths.cifar10n_root,
        noise_type=config.data.noise_type
    )
    
    # Step 2: Create model (using config.model)
    if config.model.checkpoint_path:
        model = load_checkpoint(config.model.checkpoint_path)
    else:
        model = create_model(
            architecture=config.model.architecture,
            dinov2_model=config.model.dinov2_model,
            hidden_dim=config.model.hidden_dim,
            dropout=config.model.dropout
        )
    
    # Step 3: Train (using config.training)
    trainer = Trainer(
        model=model,
        train_loader=train_loader,
        epochs=config.training.epochs,
        learning_rate=config.training.learning_rate,
        weight_decay=config.training.weight_decay
    )
    trainer.train()
    
    # Step 4: Evaluate (using config.evaluation)
    if config.evaluation.mc_passes > 0:
        # MC Dropout enabled
        mc_preds = mc_forward_efficient(
            model,
            eval_loader,
            n_passes=config.evaluation.mc_passes
        )
    else:
        # Deterministic baseline
        mc_preds = model(eval_data)
    
    # Calculate signals and metrics
    signals = calculate_signals(mc_preds)
    auroc = binary_auroc(signals, labels)
    
    # Save results
    save_results(config.paths.results_base_dir, auroc, signals)
```

## Batching Implementation

```python
# 6_ui/batch_builder.py
from backend.app.domain.models import ExperimentConfig

class BatchBuilder:
    """Builds multiple configs from sweep specification"""
    
    def build_aleatoric_batch(
        self,
        base_config: ExperimentConfig,
        noise_values: List[float]
    ) -> List[ExperimentConfig]:
        """Generate configs for aleatoric sweep"""
        configs = []
        for noise in noise_values:
            # Deep copy base config
            config = base_config.model_copy(deep=True)
            # Modify swept parameter
            config.data.aleatoric_noise_percentage = noise
            configs.append(config)
        return configs
    
    def build_epistemic_batch(
        self,
        base_config: ExperimentConfig,
        size_values: List[int]
    ) -> List[ExperimentConfig]:
        """Generate configs for epistemic sweep"""
        configs = []
        for size in size_values:
            config = base_config.model_copy(deep=True)
            config.data.under_train_per_class = size
            configs.append(config)
        return configs
```

## Migration Steps

### 1. Update backend/app/domain/models.py

```python
# Rename TrainingConfig → ExperimentConfig
# Keep nested structure (already correct)
class ExperimentConfig(BaseModel):
    """Complete experiment configuration"""
    seed: int = 42
    device: str = "auto"
    data: DataConfig
    model: ModelConfig
    training: TrainingRuntimeConfig
    evaluation: EvaluationConfig
    paths: PathsConfig
```

### 2. Update all imports

```python
# OLD
from backend.app.domain.models import TrainingConfig

# NEW
from backend.app.domain.models import ExperimentConfig
```

### 3. Update API endpoints

```python
# backend/app/api/routes/experiments.py
class ExperimentCreate(BaseModel):
    name: str
    config: ExperimentConfig  # ✅ Nested structure
```

### 4. Update Streamlit forms

Use the form components shown above that return typed Pydantic models.

## Summary

✅ **Correct naming**: `ExperimentConfig` (not `TrainingConfig`)
✅ **Nested structure**: `config.training.epochs` (not `config.epochs`)
✅ **Folder mapping**: Each section maps to a numbered folder
✅ **Correct defaults**: ResNet baseline, MC Dropout=0
✅ **Type safety**: Pydantic validates everything
✅ **Readable**: Clear which field belongs to which step

This architecture is **clean, consistent, and self-documenting**!