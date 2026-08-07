# Small-File Root-Folder Relocation Analysis

## Goal

Identify a top-level folder whose files are all under 200–300 lines of code and determine whether it can be relocated to a more appropriate place in the repository.

## Methodology

For each non-hidden top-level directory in `/workspace`, all non-binary files were scanned and the total line count (including comments and blank lines) was recorded. The threshold was checked at both 200 and 300 lines.

| Root folder | Max file size (LoC) | Folder qualifies (<200) | Folder qualifies (<300) | Notes |
|-------------|---------------------|-------------------------|-------------------------|-------|
| `backend/`  | 1,482 (`uv.lock`)   | No                      | No                      | Large lockfile and app modules; keep at root per `ROOT_LEVEL_CLEANUP_ANALYSIS.md`. |
| `configs/`  | **64** (`configs/experiment/four_region_cifar_resnet.yaml`) | **Yes** | **Yes** | Only YAML presets and a small README. |
| `data/`     | 0 files             | N/A                     | N/A                     | Empty data directory. |
| `docs/`     | 1,224 (`docs/migration/BATCH_EXPERIMENTS_DESIGN.md`) | No | No | Documentation archive; keep at root. |
| `notebooks/`| 1,257 (`notebooks/validation/RC9l Kopie.ipynb`) | No | No | Contains large notebooks. |
| `scripts/`  | 652 (`scripts/maintenance/dependency_visualizer.py`) | No | No | Mix of small and medium scripts. |
| `src/`      | 923 (`src/uqlab_core/run_artifacts.py`) | No | No | Source package with many modules. |
| `tests/`    | 473 (`tests/test_uncertainty_metrics.py`) | No | No | Test suite. |
| `uqlab-flask/`| 652 (`uqlab-flask/uqlab_flask/executor.py`) | No | No | Looks small but the executor is large; not a candidate. |

## Candidate: `configs/`

`configs/` is the only top-level folder where every file is under both 200 and 300 lines of code. Its contents are small, runnable YAML experiment presets used by the CLI, notebooks, and validation scripts.

### Current layout

```
configs/
├── README.md
├── example_cnn_mcdropout.yaml
├── example_resnet18_mcdropout.yaml
├── experiment/
│   ├── default.yaml
│   ├── fast_pilot.yaml
│   ├── four_region.yaml
│   ├── four_region_cifar_resnet.yaml
│   └── four_region_fashion_mlp.yaml
└── test/
    ├── test_cnn_mcdropout.yaml
    ├── test_dinov2_mlp.yaml
    └── test_resnet18_mcdropout.yaml
```

### Where it could go

The natural new home is under the core package, because the presets are consumed almost exclusively by `uqlab_core`:

```
src/uqlab_core/configs/
├── experiment/
├── test/
└── README.md
```

### Why this is not a trivial move

`configs/` is referenced from many places outside the core package:

- `src/uqlab_core/runtime_paths.py` defines `configs_dir() = repository_root() / "configs"`.
- `src/uqlab_core/shared/config/classification.py` defaults to `configs/fast_uq_classification.yaml`.
- `src/uqlab_core/runner/notebook_run.py` resolves notebooks against `configs/`.
- `scripts/setup/validate_architectures.py` and `scripts/setup/generate_thesis_diagram.py` hardcode `configs/`.
- Several notebooks embed `configs/` paths.
- Multiple markdown guides (`README.md`, `START_HERE.md`, `EXECUTION_FLOW_AND_CONFIG_GUIDE.md`, `docs/migration/HYDRA_GUIDE.md`, etc.) point users to `configs/`.

A physical relocation would require updating the runtime helper, the CLI default, the notebook references, and all documentation. If the move is done later, the safest approach is to keep a root-level `configs` symlink pointing to the new location during a transition period, or to update `configs_dir()` to the new path and run the full test suite.

## Recommendation

- **Keep `configs/` at the repository root for now.** The existing `ROOT_LEVEL_CLEANUP_ANALYSIS.md` already designates `configs/` as a root-level folder that should stay, and the small file size alone does not justify a broad refactor across source code, notebooks, scripts, and docs.
- **If a relocation is still desired**, the target should be `src/uqlab_core/configs/`, with a symlink `configs -> src/uqlab_core/configs` to preserve existing references while the migration is completed.
- **No other top-level folder** qualifies as all-files-under-200/300-LoC, so `configs/` is the only candidate.

## References

- `docs/development/ROOT_LEVEL_CLEANUP_ANALYSIS.md` — the canonical plan for which top-level folders should remain at the root.
- `docs/development/FILE_ORGANIZATION_ANALYSIS.md` — prior analysis on moving files based on responsibility rather than size.
- `src/uqlab_core/runtime_paths.py` — the runtime helper that locates `configs/`.
