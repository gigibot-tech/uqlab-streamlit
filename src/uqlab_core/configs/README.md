# Experiment YAML configs

Runnable experiment configs for CLI, notebooks, and validation scripts.

```
configs/
├── experiment/          # Primary experiment presets
│   ├── default.yaml
│   ├── fast_pilot.yaml
│   └── four_region.yaml   ← CLI default (run_fast_uncertainty_classification.py)
├── test/                # Architecture smoke configs (validate_architectures.py)
├── example_cnn_mcdropout.yaml
└── example_resnet18_mcdropout.yaml
```

Load in Python:

```python
from pathlib import Path
from uqlab.runtime_paths import configs_dir
from uqlab.shared.config.classification import ExperimentConfig

config = ExperimentConfig.from_yaml(configs_dir() / "experiment" / "four_region.yaml")
```

Migration notes: `docs/setup/CONFIG_AND_IMPORTS_STATUS.md`.
