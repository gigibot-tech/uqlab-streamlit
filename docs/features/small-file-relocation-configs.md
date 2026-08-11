# Small-file relocation: `configs/` → `src/uqlab_core/configs/`

## Motivation

The root-level `configs/` folder contained only small YAML files (max 64 lines, 362 total LoC). Keeping it at the repository root added clutter and separated experiment presets from the package code that consumes them.

## Decision

Relocate `configs/` into the `uqlab_core` package so that:

- Experiment presets live next to the code that loads and runs them.
- The repository root is reduced to entry points, documentation, and top-level orchestration folders.
- Configs can be shipped as package data when `uqlab_core` is installed.

## What changed

| Before | After |
|--------|-------|
| `configs/README.md` | `src/uqlab_core/configs/README.md` |
| `configs/experiment/*.yaml` | `src/uqlab_core/configs/experiment/*.yaml` |
| `configs/test/*.yaml` | `src/uqlab_core/configs/test/*.yaml` |
| `configs/example_*.yaml` | `src/uqlab_core/configs/example_*.yaml` |
| `runtime_paths.configs_dir()` → `<repo>/configs` | `runtime_paths.configs_dir()` → `<uqlab_core>/configs` |

## Updated code paths

- `src/uqlab_core/runtime_paths.py` — `configs_dir()` now returns the package-local directory.
- `src/uqlab_core/runner/notebook_run.py` — four-region benchmark presets use `configs_dir()`.
- `src/uqlab_core/shared/config/classification.py` — CLI default uses `configs_dir() / "experiment" / "four_region.yaml"`.
- `scripts/setup/validate_architectures.py` — points to `src/uqlab_core/configs/test/...`.
- `scripts/setup/generate_thesis_diagram.py` — docstring example updated.
- `src/uqlab_core/pyproject.toml` — package data includes `*.yaml` and `*.md` under `uqlab_core.configs`.

## Updated docs and notebooks

- `README.md`, `START_HERE.md`, `EXECUTION_FLOW_AND_CONFIG_GUIDE.md`
- `docs/development/ROOT_LEVEL_CLEANUP_ANALYSIS.md`
- `docs/setup/CONFIG_AND_IMPORTS_STATUS.md`
- `docs/user-guides/README_PARENT.md`
- `docs/features/ATTRIBUTION_ARTIFACTS.md`, `docs/features/disentanglement-benchmark.md`
- `docs/migration/HYDRA_GUIDE.md`, `docs/migration/MIGRATION_GUIDE.md`
- `docs/phases/PHASE7_1_ARCHITECTURE_SELECTOR.md`
- `notebooks/attribution_distribution_uncertainty.ipynb`
- `notebooks/cifar10_paper_flow.ipynb`
- `notebooks/resnet_baseline_experiment.ipynb`
- `notebooks/watsonx_deployment_experiment.ipynb`
- `notebooks/validation/RC9l Kopie.ipynb`

## Verification

```bash
PYTHONPATH=src python3 -c "from uqlab_core.runtime_paths import configs_dir; print(configs_dir())"
```

Should print the absolute path to `src/uqlab_core/configs`.

All modified Python files are compiled with `py_compile` to catch syntax/import errors.

## Result

`configs/` is no longer at the repository root. The only YAML presets live inside `src/uqlab_core/configs/`, accessible via `configs_dir()`.
