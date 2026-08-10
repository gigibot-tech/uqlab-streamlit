# Small-file relocation: `configs/`

**Status**: Completed  
**Branch**: `cursor/small-file-relocation-candidates-fb70`

## Goal

Move one root-level folder whose files are small enough to live inside the consuming package, reducing clutter at the repository root and keeping related artifacts together.

## Candidate analysis

| Folder | Files | Max LoC | Verdict |
|--------|-------|---------|---------|
| `configs/` | 11 | 64 | ✅ Move into `uqlab_core` package |
| `data/` | 1 (`.gitkeep`) | 0 | Too trivial, kept as data mount point |
| `uqlab-flask/` | 18 | 652 | Mixed sizes; not a clean candidate |
| `scripts/` | 59 | varied | Large, stay at root |
| `tests/` | 63 | varied | Large, stay at root |
| `backend/` | 113 | varied | Large, stay at root |

`configs/` was selected because every YAML file is under 200/300 LoC (max 64 LoC) and the configs are consumed almost exclusively by `uqlab_core`.

## What changed

### Relocation

```
configs/                          →  src/uqlab_core/configs/
├── example_cnn_mcdropout.yaml
├── example_resnet18_mcdropout.yaml
├── experiment/
│   ├── default.yaml
│   ├── fast_pilot.yaml
│   ├── four_region.yaml
│   ├── four_region_cifar_resnet.yaml
│   └── four_region_fashion_mlp.yaml
├── test/
│   ├── test_cnn_mcdropout.yaml
│   ├── test_dinov2_mlp.yaml
│   └── test_resnet18_mcdropout.yaml
└── README.md
```

### Code updates

| File | Change |
|------|--------|
| `src/uqlab_core/runtime_paths.py` | `configs_dir()` now returns `Path(__file__).resolve().parent / "configs"` |
| `src/uqlab_core/runner/notebook_run.py` | `default_four_region_runs()` uses `configs_dir()` for preset paths |
| `src/uqlab_core/shared/config/classification.py` | Default CLI `--config` path and docstring updated |
| `scripts/setup/validate_architectures.py` | Test config path updated to `src/uqlab_core/configs/test/...` |
| `scripts/setup/generate_thesis_diagram.py` | Docstring example updated |

### Documentation and notebooks

Updated references in:

- `README.md`
- `START_HERE.md`
- `EXECUTION_FLOW_AND_CONFIG_GUIDE.md`
- `src/uqlab_core/configs/README.md`
- `docs/setup/CONFIG_AND_IMPORTS_STATUS.md`
- `docs/features/disentanglement-benchmark.md`
- `docs/features/ATTRIBUTION_ARTIFACTS.md`
- `docs/migration/MIGRATION_GUIDE.md`
- `docs/migration/HYDRA_GUIDE.md`
- `docs/phases/PHASE7_1_ARCHITECTURE_SELECTOR.md`
- `docs/user-guides/README_PARENT.md`
- `docs/development/ROOT_LEVEL_CLEANUP_ANALYSIS.md`
- `notebooks/cifar10_paper_flow.ipynb`
- `notebooks/attribution_distribution_uncertainty.ipynb`
- `notebooks/validation/RC9l Kopie.ipynb`
- `notebooks/resnet_baseline_experiment.ipynb`
- `notebooks/watsonx_deployment_experiment.ipynb`

## Verification

```bash
PYTHONPATH=src python3 -c \
  "from uqlab_core.runtime_paths import configs_dir; print(configs_dir())"
# /workspace/src/uqlab_core/configs
```

All YAML files in the new location load successfully and the modified Python files pass `py_compile`.

## Remaining work

None. The `configs/` folder has been fully relocated and all known references updated.
