# Small Root Folder Relocation Candidates

## Check criteria

- Scan every directory located directly under the repository root.
- A folder is a candidate if **every** file inside it is ≤ 200 LoC (strict) or ≤ 300 LoC (lenient).
- Skip version control, virtual environments, well-scoped packages (e.g. `src`, `backend`, `tests`, `docs`, `scripts`), and empty/data-only folders.

## Result

| Folder | Max file LoC | Status | Proposed target |
|--------|--------------|--------|-----------------|
| `configs/` | 64 | ✅ All files ≤ 200 LoC | `src/uqlab_core/configs/` |
| `data/` | 1 | Empty / data-only | Keep at root |
| `backend/app/` | 298 | Close to limit, well-scoped backend module | Keep |
| `uqlab-flask/` | 652 | Contains large `executor.py` | Keep |
| `notebooks/validation/` | 505 | Mixed sizes, not root-level | Keep |
| `scripts/setup/` | 309 | One file over 300 | Keep |

## Relocation executed

`configs/` was the only root folder that satisfied the small-file criterion. It has been relocated to `src/uqlab_core/configs/` so the YAML experiment presets live next to the code that owns them (`runtime_paths`, `ExperimentConfig`, runners).

### Files moved

```text
configs/README.md                         → src/uqlab_core/configs/README.md
configs/example_cnn_mcdropout.yaml        → src/uqlab_core/configs/example_cnn_mcdropout.yaml
configs/example_resnet18_mcdropout.yaml   → src/uqlab_core/configs/example_resnet18_mcdropout.yaml
configs/experiment/*.yaml                 → src/uqlab_core/configs/experiment/
configs/test/*.yaml                       → src/uqlab_core/configs/test/
```

### References updated

- `src/uqlab_core/runtime_paths.py` — `configs_dir()` now resolves to `src/uqlab_core/configs/`.
- `src/uqlab_core/shared/config/classification.py` — docstring and CLI default updated.
- `src/uqlab_core/runner/notebook_run.py` — preset paths updated.
- Runner and setup scripts (`scripts/runners/run_fast_uncertainty_classification.py`, `scripts/setup/validate_architectures.py`, `scripts/setup/generate_thesis_diagram.py`).
- README, START_HERE, and execution guide.
- Migration, Hydra, and feature docs.
- Notebooks that load the preset YAMLs.

## Verification

```python
from uqlab_core.runtime_paths import configs_dir
configs_dir()  # → <repo>/src/uqlab_core/configs
list(configs_dir().glob("**/*.yaml"))  # 10 YAML presets
```
