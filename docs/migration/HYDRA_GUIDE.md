# Hydra Integration Guide (Optional)

This guide explains how to use Hydra for advanced configuration management. **Hydra is completely optional** - all existing code works without it.

## What is Hydra?

[Hydra](https://hydra.cc/) is a framework for elegantly configuring complex applications. It provides:

- **Config composition**: Combine multiple YAML files
- **Command-line overrides**: Change parameters without editing files
- **Multi-run sweeps**: Run parameter grid searches easily
- **Experiment tracking**: Automatic output directory management

## Installation

```bash
# Optional - only if you want Hydra features
pip install hydra-core
```

## Quick Start

### 1. Basic Usage

```python
# train_with_hydra.py
import hydra
from omegaconf import DictConfig
from uq_classification.hydra_wrapper import hydra_to_dataclass

@hydra.main(version_base=None, config_path="configs", config_name="experiment/default")
def main(cfg: DictConfig):
    # Convert Hydra config to validated dataclass
    config = hydra_to_dataclass(cfg)
    config.validate()
    
    print(f"Running with noise_type: {config.data.noise_type}")
    print(f"Model: {config.model.dinov2_model}")
    
    # Run your experiment
    # run_experiment(config)

if __name__ == "__main__":
    main()
```

### 2. Run with Different Configs

```bash
# Use default config
python train_with_hydra.py

# Override single parameter
python train_with_hydra.py training.epochs=20

# Override multiple parameters
python train_with_hydra.py training.epochs=20 model.hidden_dim=512

# Use different config file
python train_with_hydra.py experiment=fast_pilot

# Combine configs
python train_with_hydra.py experiment=fast_pilot training.epochs=10
```

## Config Structure

```
configs/
├── experiment/
│   ├── default.yaml       # Default configuration
│   └── fast_pilot.yaml    # Quick testing config
└── config.yaml            # (optional) Main config
```

### Default Config (`configs/experiment/default.yaml`)

```yaml
seed: 42
device: auto

data:
  noise_type: worse_label
  under_supported_classes: "3,5"
  under_train_per_class: 50
  regular_train_per_class: 300
  eval_per_group: 600

model:
  dinov2_model: small
  hidden_dim: 256
  dropout: 0.2

training:
  epochs: 12
  learning_rate: 0.001
  weight_decay: 0.0001
  train_batch_size: 256

evaluation:
  mc_passes: 20
  top_k: 10
```

### Fast Pilot Config (`configs/experiment/fast_pilot.yaml`)

```yaml
defaults:
  - default  # Inherit from default

# Override for faster experiments
data:
  under_train_per_class: 20
  regular_train_per_class: 100
  eval_per_group: 200

training:
  epochs: 5
  train_batch_size: 128

evaluation:
  mc_passes: 10
```

## Advanced Features

### 1. Parameter Sweeps

Run multiple experiments with different parameters:

```bash
# Sweep over hidden dimensions
python train_with_hydra.py -m model.hidden_dim=128,256,512

# Sweep over multiple parameters
python train_with_hydra.py -m \
  model.hidden_dim=128,256,512 \
  training.learning_rate=0.0001,0.001,0.01

# Sweep with config groups
python train_with_hydra.py -m experiment=default,fast_pilot
```

### 2. Output Directory Management

Hydra automatically creates output directories:

```bash
outputs/
└── 2024-01-15/
    └── 10-30-45/
        ├── .hydra/
        │   ├── config.yaml      # Full resolved config
        │   ├── hydra.yaml       # Hydra settings
        │   └── overrides.yaml   # CLI overrides
        └── experiment_results/  # Your outputs
```

### 3. Config Groups

Create config groups for different scenarios:

```
configs/
├── experiment/
│   ├── default.yaml
│   ├── fast_pilot.yaml
│   └── production.yaml
├── model/
│   ├── small.yaml
│   ├── base.yaml
│   └── large.yaml
└── data/
    ├── cifar10n_clean.yaml
    └── cifar10n_noisy.yaml
```

Use with:

```bash
python train_with_hydra.py \
  experiment=production \
  model=large \
  data=cifar10n_noisy
```

## Integration with Existing Code

### Option 1: Hydra Wrapper (Recommended)

```python
import hydra
from omegaconf import DictConfig
from uq_classification.hydra_wrapper import hydra_to_dataclass

@hydra.main(version_base=None, config_path="configs", config_name="experiment/default")
def main(cfg: DictConfig):
    # Convert to our dataclass (with validation)
    config = hydra_to_dataclass(cfg)
    config.validate()
    
    # Use with existing code
    from scripts.run_fast_uncertainty_classification import run_experiment
    run_experiment(config.to_dict())

if __name__ == "__main__":
    main()
```

### Option 2: Direct OmegaConf

```python
import hydra
from omegaconf import DictConfig, OmegaConf

@hydra.main(version_base=None, config_path="configs", config_name="experiment/default")
def main(cfg: DictConfig):
    # Convert to plain dict
    config_dict = OmegaConf.to_container(cfg, resolve=True)
    
    # Use with existing code
    from scripts.run_fast_uncertainty_classification import run_experiment
    run_experiment(config_dict)

if __name__ == "__main__":
    main()
```

## Comparison: With vs Without Hydra

### Without Hydra (Current Approach)

```python
# Load config
import yaml
config_dict = yaml.safe_load(open("config.yaml"))

# Modify for experiment
config_dict['training']['epochs'] = 20
config_dict['model']['hidden_dim'] = 512

# Run
run_experiment(config_dict)
```

**Pros**: Simple, no dependencies
**Cons**: Manual config management, no sweep support

### With Hydra (Optional Enhancement)

```bash
# Run with overrides
python train_with_hydra.py training.epochs=20 model.hidden_dim=512

# Run sweep
python train_with_hydra.py -m model.hidden_dim=128,256,512
```

**Pros**: Clean CLI, sweeps, experiment tracking
**Cons**: Additional dependency

## Best Practices

### 1. Keep Configs Simple

```yaml
# Good - flat and readable
data:
  noise_type: worse_label
  under_train_per_class: 50

# Avoid - too nested
data:
  sampling:
    under_supported:
      per_class: 50
```

### 2. Use Defaults for Inheritance

```yaml
# fast_pilot.yaml
defaults:
  - default  # Inherit everything

# Only override what changes
training:
  epochs: 5
```

### 3. Validate After Loading

```python
@hydra.main(...)
def main(cfg: DictConfig):
    config = hydra_to_dataclass(cfg)
    config.validate()  # Always validate!
    # ...
```

### 4. Document Overrides

```bash
# Good - clear what's being changed
python train.py training.epochs=20  # Quick test

# Better - use config groups
python train.py experiment=fast_pilot  # Pre-defined fast config
```

## Troubleshooting

### "hydra not found"

```bash
pip install hydra-core
```

Hydra is optional - code works without it.

### "Config file not found"

Check `config_path` in `@hydra.main`:

```python
@hydra.main(
    version_base=None,
    config_path="configs",  # Relative to script location
    config_name="experiment/default"
)
```

### "Override not working"

Use dot notation for nested configs:

```bash
# Correct
python train.py training.epochs=20

# Wrong
python train.py training:epochs=20
```

## Migration Guide

### Step 1: Create Hydra Configs

```bash
mkdir -p configs/experiment
# Copy your existing YAML to configs/experiment/default.yaml
```

### Step 2: Create Hydra Script

```python
# train_with_hydra.py
import hydra
from omegaconf import DictConfig
from uq_classification.hydra_wrapper import hydra_to_dataclass

@hydra.main(version_base=None, config_path="configs", config_name="experiment/default")
def main(cfg: DictConfig):
    config = hydra_to_dataclass(cfg)
    config.validate()
    
    # Use your existing training code
    from scripts.run_fast_uncertainty_classification import main as run_experiment
    run_experiment()  # Adapt as needed

if __name__ == "__main__":
    main()
```

### Step 3: Test

```bash
# Test basic run
python train_with_hydra.py

# Test override
python train_with_hydra.py training.epochs=5

# Test sweep
python train_with_hydra.py -m training.epochs=5,10,15
```

## Examples

### Example 1: Quick Hyperparameter Search

```bash
# Search over learning rates and hidden dimensions
python train_with_hydra.py -m \
  training.learning_rate=0.0001,0.001,0.01 \
  model.hidden_dim=128,256,512
# Runs 9 experiments (3 × 3 grid)
```

### Example 2: Reproducible Experiments

```bash
# Run with specific seed
python train_with_hydra.py seed=42

# Results saved to outputs/YYYY-MM-DD/HH-MM-SS/
# Config automatically saved for reproducibility
```

### Example 3: Config Composition

```yaml
# configs/experiment/ablation.yaml
defaults:
  - default
  - override model: large  # Use large model config
  - override data: noisy   # Use noisy data config

# Only specify what's unique to this ablation
training:
  epochs: 50
```

## Summary

| Feature | Without Hydra | With Hydra |
|---------|---------------|------------|
| Config loading | ✅ YAML | ✅ YAML + composition |
| CLI overrides | ❌ Manual | ✅ Automatic |
| Parameter sweeps | ❌ Manual loops | ✅ Built-in |
| Experiment tracking | ❌ Manual | ✅ Automatic |
| Complexity | Low | Medium |
| Dependencies | None | hydra-core |

**Recommendation**: Start without Hydra. Add it later if you need sweeps or complex config management.

## Resources

- [Hydra Documentation](https://hydra.cc/)
- [Hydra Tutorials](https://hydra.cc/docs/tutorials/intro/)
- [Config Groups](https://hydra.cc/docs/tutorials/basic/your_first_app/config_groups/)
- [Multi-run](https://hydra.cc/docs/tutorials/basic/running_your_app/multi-run/)

## Made with Bob