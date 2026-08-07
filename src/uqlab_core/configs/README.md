# Experiment YAML configs

Runnable experiment configs for CLI, notebooks, and validation scripts.

## Canonical location

These files now live inside the `uqlab_core` package:

```
src/uqlab_core/configs/
├── experiment/          # Primary experiment presets
│   ├── default.yaml
│   ├── fast_pilot.yaml
│   └── four_region.yaml   ← CLI default (run_fast_uncertainty_classification.py)
├── test/                # Architecture smoke configs (validate_architectures.py)
├── example_cnn_mcdropout.yaml
└── example_resnet18_mcdropout.yaml
```

A root-level `configs` symlink is kept for backward compatibility, so existing docs, notebooks, and CLI commands such as `--config configs/experiment/four_region.yaml` continue to work.

Load in Python:

```python
from pathlib import Path
from uqlab_core.runtime_paths import configs_dir
from uqlab_core.shared.config.classification import ExperimentConfig

config = ExperimentConfig.from_yaml(configs_dir() / "experiment" / "four_region.yaml")
```

Migration notes: `docs/setup/CONFIG_AND_IMPORTS_STATUS.md`.
