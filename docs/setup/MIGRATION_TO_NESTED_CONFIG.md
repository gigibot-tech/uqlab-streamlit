# Migration Guide: Flat Config → Nested Config

## Overview

We're migrating from a **flat config structure** to a **nested config structure** that maps cleanly to our folder organization (1_data/, 2_models/, 3_training/, 4_evaluation/).

## Why This Change?

### Before (FLAT - Confusing)
```python
config = {
    "noise_type": "worse_label",      # Data field
    "architecture": "resnet",          # Model field
    "epochs": 12,                      # Training field
    "mc_passes": 0,                    # Evaluation field
    # ... 20+ fields mixed together
}
```

**Problems:**
- Hard to see which field belongs to which step
- No clear mapping to folder structure
- Difficult to understand config at a glance

### After (NESTED - Clear)
```python
config = {
    "seed": 42,
    "device": "auto",
    "data": {                          # 1_data/
        "noise_type": "worse_label",
        "under_train_per_class": 50,
        ...
    },
    "model": {                         # 2_models/
        "architecture": "resnet18_mcdropout",
        "hidden_dim": 256,
        ...
    },
    "training": {                      # 3_training/
        "epochs": 12,
        "learning_rate": 0.001,
        ...
    },
    "evaluation": {                    # 4_evaluation/
        "mc_passes": 0,
        "attribution_method": "dualxda",
        ...
    },
    "paths": {
        "cifar10n_root": "./data/cifar10n",
        ...
    }
}
```

**Benefits:**
- ✅ Clear section boundaries
- ✅ Maps to folder structure (1→2→3→4)
- ✅ Self-documenting
- ✅ Easy to understand and modify

## Key Changes

### 1. Backend Models (`backend/app/domain/models.py`)

**NEW: ExperimentConfig (Recommended)**
```python
from backend.app.domain.models import ExperimentConfig

# Create nested config
config = ExperimentConfig(
    seed=42,
    device="auto",
    data=DataConfig(...),
    model=ModelConfig(...),
    training=TrainingRuntimeConfig(...),
    evaluation=EvaluationConfig(...),
    paths=PathsConfig(...)
)

# Access nested fields
config.data.noise_type
config.model.architecture
config.training.epochs
config.evaluation.mc_passes
```

**OLD: TrainingConfig (Deprecated)**
```python
from backend.app.domain.models import TrainingConfig

# Still works but deprecated
config = TrainingConfig(
    noise_type="worse_label",  # Flat
    architecture="resnet",
    epochs=12,
    mc_passes=0
)
```

### 2. Correct Defaults

**IMPORTANT**: Defaults have been corrected!

| Field | OLD Default | NEW Default | Reason |
|-------|-------------|-------------|--------|
| `model.architecture` | `"dinov2_mlp"` | `"resnet18_mcdropout"` | ResNet is the baseline |
| `evaluation.mc_passes` | `20` | `0` | MC Dropout disabled by default |

### 3. UI Components

**NEW: build_nested_experiment_config()**
```python
from uqlab.ui_components import build_nested_experiment_config

config = build_nested_experiment_config(
    noise_type="worse_label",
    under_supported="3,5",
    under_train_per_class=50,
    regular_train_per_class=300,
    dinov2_model="small",
    hidden_dim=256,
    dropout=0.2,
    epochs=12,
    learning_rate=0.001,
    weight_decay=0.0001,
    train_batch_size=256,
    eval_per_group=600,
    mc_passes=0,  # ✅ Default: 0
    architecture="resnet18_mcdropout",  # ✅ Default: ResNet
)

# Returns nested dict:
# {
#     "seed": 42,
#     "device": "auto",
#     "data": {...},
#     "model": {...},
#     "training": {...},
#     "evaluation": {...},
#     "paths": {...}
# }
```

**OLD: build_base_experiment_config() (Still works)**
```python
from uqlab.ui_components import build_base_experiment_config

# Returns flat dict (backward compatible)
config = build_base_experiment_config(...)
```

## Migration Steps

### Step 1: Update Imports

```python
# OLD
from backend.app.domain.models import TrainingConfig

# NEW
from backend.app.domain.models import ExperimentConfig, DataConfig, ModelConfig, TrainingRuntimeConfig, EvaluationConfig, PathsConfig
```

### Step 2: Update Config Creation

**Option A: Use Pydantic Models (Type-Safe)**
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
        mc_passes=0,
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

**Option B: Use Helper Function**
```python
from uqlab.ui_components import build_nested_experiment_config

config = build_nested_experiment_config(
    noise_type="worse_label",
    under_supported="3,5",
    under_train_per_class=50,
    regular_train_per_class=300,
    dinov2_model="small",
    hidden_dim=256,
    dropout=0.2,
    epochs=12,
    learning_rate=0.001,
    weight_decay=0.0001,
    train_batch_size=256,
    eval_per_group=600,
    mc_passes=0,
    architecture="resnet18_mcdropout"
)
```

### Step 3: Update Field Access

```python
# OLD (flat)
noise_type = config["noise_type"]
architecture = config["architecture"]
epochs = config["epochs"]
mc_passes = config["mc_passes"]

# NEW (nested)
noise_type = config["data"]["noise_type"]
architecture = config["model"]["architecture"]
epochs = config["training"]["epochs"]
mc_passes = config["evaluation"]["mc_passes"]
```

### Step 4: Update API Calls

```python
# API accepts both formats!

# Option 1: Send nested dict
response = requests.post(
    f"{API_URL}/api/v1/experiments/no-auth",
    json={
        "name": "my_experiment",
        "config": config  # Nested dict
    }
)

# Option 2: Send Pydantic model
response = requests.post(
    f"{API_URL}/api/v1/experiments/no-auth",
    json={
        "name": "my_experiment",
        "config": config.model_dump()  # Convert to dict
    }
)
```

## Backward Compatibility

### The API Accepts Both Formats!

The backend automatically detects and converts between formats:

```python
# backend/app/domain/models.py

class TrainingConfig(BaseModel):
    """DEPRECATED but still works"""
    
    @classmethod
    def from_legacy_flat_dict(cls, payload: Dict[str, Any]) -> "TrainingConfig":
        """Handles both flat and nested payloads"""
        if any(key in payload for key in ("data", "model", "training", "evaluation")):
            # Nested format detected - convert to flat
            return cls(
                noise_type=payload["data"]["noise_type"],
                architecture=payload["model"]["architecture"],
                epochs=payload["training"]["epochs"],
                mc_passes=payload["evaluation"]["mc_passes"],
                ...
            )
        else:
            # Flat format - use directly
            return cls(**payload)
```

### Converting Between Formats

```python
from backend.app.domain.models import ExperimentConfig

# Flat → Nested
flat_config = {"noise_type": "worse_label", "architecture": "resnet", ...}
nested_config = ExperimentConfig.from_flat_dict(flat_config)

# Nested → Flat
nested_config = ExperimentConfig(...)
flat_config = nested_config.to_flat_dict()
```

## Streamlit App Migration

### Progressive App (`streamlit_app_progressive.py`)

**Before:**
```python
def _build_experiment_payload(workflow, name, **kwargs):
    return {
        "name": name,
        "config": build_base_experiment_config(...)  # Flat
    }
```

**After:**
```python
def _build_experiment_payload(workflow, name, **kwargs):
    return {
        "name": name,
        "config": build_nested_experiment_config(...)  # Nested
    }
```

### Main App (`streamlit_app.py`)

**Before:**
```python
experiment_data = {
    "name": exp_name,
    "config": build_base_experiment_config(...)  # Flat
}
```

**After:**
```python
experiment_data = {
    "name": exp_name,
    "config": build_nested_experiment_config(...)  # Nested
}
```

## Testing the Migration

### 1. Test Config Creation
```python
from backend.app.domain.models import ExperimentConfig

config = ExperimentConfig()
print(config.model_dump())
# Should show nested structure
```

### 2. Test API Submission
```python
import requests

config = build_nested_experiment_config(...)
response = requests.post(
    "http://localhost:8000/api/v1/experiments/no-auth",
    json={"name": "test", "config": config}
)
print(response.json())
```

### 3. Test Backward Compatibility
```python
# Old flat config should still work
flat_config = build_base_experiment_config(...)
response = requests.post(
    "http://localhost:8000/api/v1/experiments/no-auth",
    json={"name": "test", "config": flat_config}
)
print(response.json())
```

## Checklist

- [x] Backend models updated with `ExperimentConfig`
- [x] Correct defaults applied (ResNet, MC=0)
- [x] `build_nested_experiment_config()` created
- [x] Backward compatibility maintained
- [ ] Progressive app migrated
- [ ] Main app migrated
- [ ] Tests passing
- [ ] Documentation updated

## Summary

| Aspect | OLD | NEW |
|--------|-----|-----|
| **Structure** | Flat (20+ fields) | Nested (5 sections) |
| **Model Default** | DINOv2 | ResNet ✅ |
| **MC Dropout Default** | 20 | 0 ✅ |
| **Folder Mapping** | None | Clear (1→2→3→4) ✅ |
| **Readability** | Low | High ✅ |
| **Type Safety** | Partial | Full ✅ |
| **Backward Compatible** | N/A | Yes ✅ |

The new nested structure is **cleaner, more maintainable, and self-documenting**!