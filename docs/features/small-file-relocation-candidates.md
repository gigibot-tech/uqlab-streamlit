# Small-File Root-Folder Relocation Candidates

## Goal

Find **one root-level folder** whose files are all small (strictly < 200 LoC, leniently < 300 LoC) and decide whether it — or its contents — can be relocated somewhere more appropriate.

## Methodology

1. Enumerate every directory at the repository root.
2. Count files and measure LoC per file (text files only; ignores `.git`, `.cursor`, `.vscode`, `__pycache__`, `.DS_Store`, etc.).
3. Flag folders where **every** file is below the 200/300 LoC threshold and the folder is non-trivial (> 1 file).
4. Cross-check textual references to the candidate to estimate relocation cost.

Scanner used: [`scripts/maintenance/find_small_root_folders.py`](../../scripts/maintenance/find_small_root_folders.py)

## Current scan

```
| Folder        | Files | Total LoC | Max LoC | < 200 | < 300 | Candidate |
|---------------|------:|----------:|--------:|:-----:|:-----:|:---------:|
| configs       | 11    | 426       | 64      | ✅    | ✅    | ✅        |
| data          | 1     | 0         | 0       | ✅    | ✅    | —         |
| .cursor       | 1     | 72        | 72      | ✅    | ✅    | —         |
| .vscode       | 3     | 68        | 31      | ✅    | ✅    | —         |
| backend       | 113   | 13 726    | 1 482   | ❌    | ❌    | —         |
| docs          | 347   | 59 164    | 1 224   | ❌    | ❌    | —         |
| notebooks     | 23    | 9 080     | 1 257   | ❌    | ❌    | —         |
| scripts       | 59    | 11 288    | 652     | ❌    | ❌    | —         |
| src           | 68    | 14 685    | 923     | ❌    | ❌    | —         |
| tests         | 63    | 8 305     | 473     | ❌    | ❌    | —         |
| uqlab-flask   | 18    | 1 768     | 652     | ❌    | ❌    | —         |
| .bob          | 3     | 1 620     | 663     | ❌    | ❌    | —         |
```

- Thresholds: **200 LoC** (strict) and **300 LoC** (lenient).
- `data/` contains only `.gitkeep` and is not a meaningful relocation target.
- `.cursor/` and `.vscode/` are editor/tooling folders and are intentionally kept at root.

## Candidate: `configs/`

`configs/` is the only root-level folder whose contents are **all** below the threshold **and** non-trivial.

### File inventory

```
configs/
├── example_cnn_mcdropout.yaml              44 lines
├── example_resnet18_mcdropout.yaml         40 lines
├── experiment/
│   ├── default.yaml                        45 lines
│   ├── fast_pilot.yaml                     19 lines
│   ├── four_region.yaml                    48 lines
│   ├── four_region_cifar_resnet.yaml       64 lines
│   └── four_region_fashion_mlp.yaml        64 lines
├── test/
│   ├── test_cnn_mcdropout.yaml             26 lines
│   ├── test_dinov2_mlp.yaml                25 lines
│   └── test_resnet18_mcdropout.yaml        25 lines
└── README.md                               26 lines
```

- **Total files:** 11
- **Largest file:** `four_region_cifar_resnet.yaml` / `four_region_fashion_mlp.yaml` at 64 lines
- **All files are below 100 LoC**, well under both the 200 and 300 LoC thresholds.

## What `configs/` contains

Runnable YAML experiment presets consumed by:

- CLI runners: `scripts/runners/run_fast_uncertainty_classification.py`, `scripts/runners/run_validation_experiments.py`.
- Validation helpers: `scripts/setup/validate_architectures.py`.
- Notebooks: `notebooks/cifar10_paper_flow.ipynb`, `notebooks/attribution_distribution_uncertainty.ipynb`, `notebooks/resnet_baseline_experiment.ipynb`, etc.
- Documentation: `README.md`, `START_HERE.md`, `EXECUTION_FLOW_AND_CONFIG_GUIDE.md`, docs in `docs/migration/`, `docs/setup/`, `docs/features/`, `docs/phases/`, and `docs/user-guides/`.
- The runtime-path helper `src/uqlab_core/runtime_paths.py::configs_dir()` points directly at this directory.
- `src/uqlab_core/shared/config/classification.py` implements default-override resolution that assumes YAML references live under `configs/`.

## Can it be moved?

**Not without a coordinated migration.**

The scanner finds **48 textual references** to `configs/` across markdown, Python, YAML, shell, and Jupyter notebook files (excluding this analysis doc). Moving the folder would break:

- Notebook cells that resolve `ROOT / "configs/experiment/..."`.
- CLI examples in user-facing docs.
- `configs_dir()` in `runtime_paths.py`.
- Default-resolution logic in `classification.py` and the fallback default config `configs/fast_uq_classification.yaml`.

## Where it could logically live

Per [`docs/setup/CONFIG_AND_IMPORTS_STATUS.md`](../../docs/setup/CONFIG_AND_IMPORTS_STATUS.md):

> **Short term**: Keep using YAML configs in `configs/`  
> **Long term**: Migrate to Python configs in `src/uqlab/shared/config/`

Realistic destinations if a migration is undertaken:

1. **Package-bundled YAML presets:** `src/uqlab_core/configs/experiment/` and `src/uqlab_core/configs/test/`.
   - Keeps YAML runnable while eliminating a root-level folder.
   - Requires updating `runtime_paths.configs_dir()` and all hard-coded references.

2. **Python config presets:** migrate YAML content into Python dataclasses under `src/uqlab_core/shared/config/`.
   - Aligns with the documented long-term plan.
   - Larger effort because callers currently expect YAML paths.

3. **Keep at root as user-facing artifacts:** leave `configs/` where it is.
   - Matches the existing recommendation in `docs/development/ROOT_LEVEL_CLEANUP_ANALYSIS.md` (`configs/` is marked **KEEP**).
   - Least risky, but does not address the small-files-at-root observation.

## Recommendation

- `configs/` is the correct answer to the question *“which root folder is composed entirely of small files?”*
- It **can** be relocated in principle, but only as part of a deliberate config-migration project.
- The immediate action is to **record the candidate** and treat relocation as a follow-up:
  1. Audit every `configs/...` path in notebooks, scripts, and docs.
  2. Decide between package-bundled YAML vs. Python config presets.
  3. Update `runtime_paths.configs_dir()` and any default-resolution logic.
  4. Move the files and update all references in one PR.

## Other folders considered

| Folder | Verdict |
|--------|---------|
| `data/` | Only `.gitkeep` (0 lines). Not a meaningful relocation target. |
| `.cursor/`, `.vscode/` | Editor settings — keep at root. |
| `uqlab-flask/` | Root files are small, but `uqlab_flask/executor.py` (652 lines), `routes/wizard.py` (282 lines), and `templates/launched.html` (276 lines) exceed the threshold. |
| `backend/`, `scripts/`, `tests/`, `src/`, `notebooks/`, `docs/` | Contain many files above the threshold. |

## Related docs

- [`docs/development/ROOT_LEVEL_CLEANUP_ANALYSIS.md`](../../docs/development/ROOT_LEVEL_CLEANUP_ANALYSIS.md) — marks `configs/` as KEEP at root.
- [`docs/setup/CONFIG_AND_IMPORTS_STATUS.md`](../../docs/setup/CONFIG_AND_IMPORTS_STATUS.md) — short-term YAML / long-term Python config strategy.
- [`src/uqlab_core/runtime_paths.py`](../../src/uqlab_core/runtime_paths.py) — `configs_dir()` abstraction.
- [`src/uqlab_core/shared/config/classification.py`](../../src/uqlab_core/shared/config/classification.py) — YAML loading and default resolution.
