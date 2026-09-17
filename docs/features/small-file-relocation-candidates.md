# Small-File Root-Folder Relocation Candidates

## Goal

Identify a top-level folder whose files are all small (< 200 LoC, ideally < 300 LoC) and evaluate whether that folder — or its contents — can be relocated into a more appropriate place in the repository.

## Methodology

1. Enumerated every top-level directory in the repo root.
2. Counted files and measured line counts per file.
3. Filtered for folders where **every** file is below the 200/300 LoC threshold.
4. Cross-checked references to the candidate folder to determine relocation feasibility.

Scanner used: [`scripts/maintenance/find_small_root_folders.py`](../../scripts/maintenance/find_small_root_folders.py)

## Current scan (run on this branch)

```
| Folder     | Files | Total LoC | Max LoC | Candidate |
|------------|------:|----------:|--------:|:---------:|
| `.cursor`  | 1     | 72        | 72      | ✅        |
| `.docs`    | 5     | 560       | 252     | ✅        |
| `.vscode`  | 3     | 68        | 31      | ✅        |
| `configs`  | 11    | 428       | 64      | ✅        |
| `backend`  | 102   | 12030     | 1393    | —         |
| `docs`     | 347   | 59164     | 1224    | —         |
| `notebooks`| 11    | 1960      | 505     | —         |
| `scripts`  | 59    | 11288     | 652     | —         |
| `src`      | 68    | 14685     | 923     | —         |
| `tests`    | 63    | 8305      | 473     | —         |
| `uqlab-flask`| 18  | 1768      | 652     | —         |
```

- Thresholds: `200 LoC` (strict) and `300 LoC` (lenient).
- `data/` contains only `.gitkeep` and is not counted as a text-file candidate.

## Candidate: `configs/`

The `configs/` directory is the only root-level folder whose contents are all below the threshold **and** non-trivial (more than one file). Editor/tooling folders (`.cursor`, `.vscode`) and the hidden `.docs` folder are intentionally kept at root.

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

These are runnable YAML experiment presets used by:

- CLI runners (`scripts/runners/run_fast_uncertainty_classification.py`, `scripts/runners/run_validation_experiments.py`)
- Validation scripts (`scripts/setup/validate_architectures.py`)
- Notebooks (`notebooks/cifar10_paper_flow.ipynb`, `notebooks/four_region_benchmark.ipynb`, etc.)
- Documentation (`START_HERE.md`, `EXECUTION_FLOW_AND_CONFIG_GUIDE.md`, docs in `docs/migration/` and `docs/features/`)
- The config loader in `src/uqlab_core/shared/config/classification.py`, which references the default/override pattern used by `fast_pilot.yaml` → `default.yaml`.
- `src/uqlab_core/runtime_paths.py` exposes `configs_dir()` pointing at this directory.

## Can it be moved?

**Not today without a coordinated migration.**

The directory is heavily referenced by hard-coded relative paths across scripts, notebooks, and documentation. The scanner reports **38 textual references** to `configs/`. Moving it would break:

- Notebook cells that do `ROOT / "configs/experiment/..."`.
- CLI examples in user-facing docs.
- The `configs_dir()` abstraction in `runtime_paths.py`.
- The default-override resolution in `load_yaml_merging_defaults`, which expects `defaults` references to live in the same directory.

## Where it could logically live

Per the existing strategy in `docs/setup/CONFIG_AND_IMPORTS_STATUS.md`:

> **Short term**: Keep using YAML configs in `configs/`  
> **Long term**: Migrate to Python configs in `src/uqlab/shared/config/`

The canonical destinations are:

1. **Package-bundled YAML presets:** `src/uqlab_core/configs/experiment/` and `src/uqlab_core/configs/test/`.
   - Keeps YAML runnable while removing a root-level folder.
   - Requires updating `runtime_paths.configs_dir()` and all hard-coded references.

2. **Python config presets:** migrate the YAML content into Python dataclasses under `src/uqlab_core/shared/config/`.
   - Aligns with the documented long-term plan.
   - Larger effort because callers currently expect YAML paths.

3. **Keep at root as user-facing artifacts:** leave `configs/` where it is.
   - This is what `docs/development/ROOT_LEVEL_CLEANUP_ANALYSIS.md` already recommends (`configs/` marked KEEP).
   - Least risky, but does not address the small-files-at-root observation.

## Recommendation

- `configs/` is the correct answer to the question “which root folder is composed entirely of small files?”
- It **can** be relocated in principle, but only as part of a deliberate config-migration effort.
- The immediate action is to **record the candidate** and treat relocation as a follow-up project:
  1. Audit every `configs/...` path in notebooks, scripts, and docs.
  2. Decide between package-bundled YAML vs. Python config presets.
  3. Update `runtime_paths.configs_dir()` and any default-resolution logic.
  4. Move the files and update all references in one PR.

## Other folders considered

| Folder | Verdict |
|--------|---------|
| `data/` | Only contains `.gitkeep` (0 lines). Not a meaningful relocation target. |
| `.cursor/`, `.vscode/` | IDE/editor settings — keep at root. |
| `.docs/` | Hidden docs already scheduled for relocation to `docs/setup/` / `docs/deployment/` / `docs/development/` in prior cleanup work. |
| `uqlab-flask/` | Root files are small, but `uqlab_flask/executor.py` (652 lines), `routes/wizard.py` (282 lines), and `templates/launched.html` (276 lines) exceed the threshold. |
| `backend/`, `scripts/`, `tests/`, `src/`, `notebooks/`, `docs/` | Contain many files above the threshold. |

## Related docs

- `docs/development/ROOT_LEVEL_CLEANUP_ANALYSIS.md` — marks `configs/` as KEEP at root.
- `docs/setup/CONFIG_AND_IMPORTS_STATUS.md` — outlines short-term YAML / long-term Python config strategy.
- `src/uqlab_core/runtime_paths.py` — `configs_dir()` abstraction.
- `src/uqlab_core/shared/config/classification.py` — YAML loading and default resolution.
