# Small File Relocation Candidates (8feb)

**Date:** 2026-08-09  
**Branch:** `cursor/small-file-relocation-candidates-8feb`  
**Scope:** A single root-level folder whose files are all under 200–300 lines of code and whether they can be relocated.

---

## Executive Summary

The repository root contains several top-level folders. One folder stands out as a *pure* small-file candidate: **`configs/`**.

- **11 files** in total.
- **All files are under 200 LoC** (largest = 64 LoC).
- **All files are under 300 LoC** by a wide margin.
- Files are YAML presets and a short README — no generated lockfiles, no binary files, no hidden files.

Because the directory is entirely small and self-contained, it can be moved if a more natural home is found. The recommended destination is inside the `uqlab_core` package, which is the code that consumes these YAML configs.

---

## Methodology

A file was counted as "small" if it had fewer than 200 lines of code. A secondary threshold of 300 LoC was also checked for completeness. Line counts were taken with `wc -l` and exclude hidden files, `__pycache__`, and generated lockfiles.

Root folders analyzed for this audit:

| Folder | Total files | <300 LoC | <200 LoC | Median LoC | Largest file |
|--------|-------------|----------|----------|------------|--------------|
| `configs/` | 11 | 11 (100%) | 11 (100%) | 44 | `experiment/four_region_cifar_resnet.yaml` / `experiment/four_region_fashion_mlp.yaml` (64) |
| `uqlab-flask/` | 18 | 17 (94.4%) | 15 (83.3%) | 25 | `uqlab_flask/executor.py` (652) |
| `backend/` | 104 | 94 (90.4%) | 87 (83.7%) | 49 | `RUN_LABEL_NOISE_SWEEP_FLOW.md` (911) |
| `scripts/` | 59 | 47 (79.7%) | 37 (62.7%) | 118 | `dependency_visualizer.py` (652) |
| `tests/` | 63 | 56 (88.9%) | 52 (82.5%) | 86 | `test_uncertainty_metrics.py` (473) |
| `notebooks/` | 23 | 11 (47.8%) | — | 303 | `validation/RC9l Kopie.ipynb` (1257) |
| `docs/` | 347 | 279 (80.4%) | — | 88 | `migration/BATCH_EXPERIMENTS_DESIGN.md` (1224) |

Only `configs/` passes both thresholds for **every** file. The other folders contain large files that disqualify them as clean, wholesale relocation candidates.

---

## Primary Candidate: `configs/`

### Current Structure

```text
configs/
├── README.md                                  26 LoC
├── example_cnn_mcdropout.yaml                44 LoC
├── example_resnet18_mcdropout.yaml           40 LoC
├── experiment/
│   ├── default.yaml                          45 LoC
│   ├── fast_pilot.yaml                       19 LoC
│   ├── four_region.yaml                      48 LoC
│   ├── four_region_cifar_resnet.yaml        64 LoC
│   └── four_region_fashion_mlp.yaml          64 LoC
└── test/
    ├── test_cnn_mcdropout.yaml               26 LoC
    ├── test_dinov2_mlp.yaml                  25 LoC
    └── test_resnet18_mcdropout.yaml          25 LoC
```

All files are small YAML experiment presets. There are no large notebooks, no generated lockfiles, and no hidden files.

### Why It Stands Out

1. **Uniform size.** Every file is under 200 LoC; the folder has no outlier files that would complicate a move.
2. **Single concern.** The directory only contains YAML experiment/test presets and a README.
3. **Root-level clutter.** `configs/` is one of the top-level folders in the repository root. Moving it would reduce the number of root-level items.
4. **Clear consumer.** The configs are loaded by `uqlab_core` (`runtime_paths.configs_dir()`, `ExperimentConfig.from_yaml()`, CLI runners, and notebooks). Placing them inside `src/uqlab_core/` keeps the data next to the code that uses it.
5. **Low risk.** Because every file is small, the move is mechanically simple; there are no large modules to split or refactor first.

### Current References

Hard-coded or semi-hard-coded references to the `configs/` directory include:

- `src/uqlab_core/runtime_paths.py` — `configs_dir()` returns `repository_root() / "configs"`.
- `src/uqlab_core/runner/notebook_run.py` — references `configs/experiment/four_region_*.yaml`.
- `src/uqlab_core/shared/config/classification.py` — docstring mentions `configs/experiment/fast_pilot.yaml`.
- `scripts/setup/validate_architectures.py` — loads `configs/test/*.yaml`.
- `scripts/setup/generate_thesis_diagram.py` — uses `configs/experiment/default.yaml`.
- `START_HERE.md` — CLI example uses `configs/experiment/four_region.yaml`.
- `EXECUTION_FLOW_AND_CONFIG_GUIDE.md` — references `configs/experiment/four_region.yaml`.
- `docs/migration/MIGRATION_GUIDE.md` and `docs/migration/HYDRA_GUIDE.md` — document the `configs/` layout.
- `docs/phases/PHASE7_1_ARCHITECTURE_SELECTOR.md` — references `configs/example_*.yaml`.
- `docs/features/disentanglement-benchmark.md` and `docs/features/ATTRIBUTION_ARTIFACTS.md` — link to config files.
- Multiple notebooks in `notebooks/` load configs from `configs/...`.

---

## Relocation Options

### Option A: Move into `src/uqlab_core/configs/` (Recommended)

Place the YAML presets inside the `uqlab_core` package, which is their primary consumer.

```text
BEFORE:
configs/
├── README.md
├── example_cnn_mcdropout.yaml
├── example_resnet18_mcdropout.yaml
├── experiment/
└── test/

AFTER:
src/uqlab_core/
├── ...
└── configs/
    ├── README.md
    ├── example_cnn_mcdropout.yaml
    ├── example_resnet18_mcdropout.yaml
    ├── experiment/
    └── test/
```

**Benefits:**
- Keeps YAML presets next to the Python code that loads and validates them.
- Removes one folder from the repository root.
- Aligns with the package-oriented layout already used by `src/uqlab_core/shared/config/` (config schemas) and `src/uqlab_core/data/` (data logic).

**Files to update:**
- `src/uqlab_core/runtime_paths.py` — change `configs_dir()` to `repository_root() / "src" / "uqlab_core" / "configs"`.
- `scripts/setup/validate_architectures.py`.
- `scripts/setup/generate_thesis_diagram.py`.
- `src/uqlab_core/runner/notebook_run.py`.
- `START_HERE.md`, `EXECUTION_FLOW_AND_CONFIG_GUIDE.md`, and feature/migration docs that embed paths.
- Notebooks that hard-code `configs/...` paths.

### Option B: Move to `examples/configs/` or `presets/`

Create a new root-level `examples/` or `presets/` folder and move the YAML files there.

**Benefits:**
- Makes it explicit that these files are example/preset configurations, not production runtime configs.

**Drawbacks:**
- Adds a *new* root folder instead of removing one, so the net root-clutter reduction is zero or negative.
- Still requires updating all `configs/` references.
- The files are actively used by the runtime (`runtime_paths.configs_dir()`), not just as examples, so the label is slightly misleading.

**Recommendation:** Not preferred.

### Option C: Keep at root but rename to `presets/`

Rename `configs/` to `presets/` and update references.

**Benefits:**
- More descriptive name for YAML presets.

**Drawbacks:**
- Does not reduce root clutter.
- Renaming is a breaking change for external notes/scripts that reference `configs/`.
- Does not solve the architectural separation issue.

**Recommendation:** Not preferred unless the root location is considered non-negotiable.

---

## Recommended Action

**Adopt Option A:** move `configs/` into `src/uqlab_core/configs/` and update `runtime_paths.configs_dir()` plus the hard-coded references in scripts, docs, and notebooks.

### Immediate Steps

1. Create `src/uqlab_core/configs/` and move all `configs/` contents into it.
2. Update `src/uqlab_core/runtime_paths.py` so `configs_dir()` points to the new location.
3. Update `scripts/setup/validate_architectures.py` and `scripts/setup/generate_thesis_diagram.py`.
4. Update `src/uqlab_core/runner/notebook_run.py`.
5. Update `START_HERE.md`, `EXECUTION_FLOW_AND_CONFIG_GUIDE.md`, and affected docs/features/migration docs.
6. Update notebooks that reference `configs/` paths.
7. Run a quick import/launch check to verify `configs_dir()` still resolves correctly.

### Deferred Steps

- If Option A is accepted and implemented, consider whether the existing `src/uqlab_core/shared/config/` (Python schemas) should be renamed or reorganized to avoid confusion with the new `src/uqlab_core/configs/` (YAML presets).

---

## Other Root Folders Considered and Rejected

| Folder | Reason not to relocate as a whole |
|--------|-----------------------------------|
| `uqlab-flask/` | Mostly small, but `executor.py` (652 LoC) and `wizard.py` (282 LoC) exceed the thresholds; a whole-folder move would drag large files along. (It is still a strong candidate for relocation, but it needs a plan that handles the large files.) |
| `backend/` | Large docs and lockfiles (`uv.lock`, `RUN_LABEL_NOISE_SWEEP_FLOW.md`) exceed thresholds; the folder is already structured as the main backend. |
| `scripts/` | Several files exceed 300 LoC (`dependency_visualizer.py`, `README.md`, etc.); the folder was already reorganized in prior work. |
| `tests/` | Many small files but also `test_uncertainty_metrics.py` (473 LoC); moving tests would break the existing layout. |
| `notebooks/` | Dominated by large `.ipynb` files; not a small-file candidate. |
| `docs/` | Documentation is intentionally granular and includes large design docs; not a candidate. |
| `data/` | Only a `.gitkeep` placeholder; not a meaningful relocation candidate. |
| `.vscode/` | Editor settings; moving would break VS Code detection and is not standard practice. |

---

## Risks

- **Hard-coded paths:** Many docs and notebooks embed `configs/...` paths. A move must update all of them.
- **Runtime path:** `uqlab.runtime_paths.configs_dir()` is the single source of truth for code that loads configs, but any external scripts that construct paths manually will break.
- **User habit:** External notes, runbooks, or bookmarks may reference `configs/`.
- **Package layout:** Moving YAML files into `src/uqlab_core/` means they are shipped with the package. Ensure this is desirable (it is, because they are runtime presets).

---

## Conclusion

`configs/` is the only root-level folder in which **every** file is under the 200/300 LoC threshold. It is small, focused, and has a clear primary consumer (`uqlab_core`). It can be relocated wholesale to `src/uqlab_core/configs/` with modest reference-updating work. Doing so would reduce root-level clutter and keep the experiment presets closer to the code that uses them.
