# Small-File Relocation Candidates

## Summary

The root-level folder **`configs/`** is the best small-file relocation candidate.

- 11 files, all under 200 LoC, totaling ~428 LoC
- Entirely YAML experiment/test presets and a small README
- Already documented as a legacy/short-term config location in [`docs/setup/CONFIG_AND_IMPORTS_STATUS.md`](../setup/CONFIG_AND_IMPORTS_STATUS.md)
- Can be moved into the active source package with mechanical reference updates

## Methodology

Scanned every non-hidden root directory and counted lines of code (total lines, including blanks/comments) for every file inside it. The goal was to find one root folder where the majority of files fall below the 200–300 LoC band and are therefore easy to relocate as a unit.

## Root-folder scan results

| Folder | Files | <200 LoC | <300 LoC | Total LoC | Notes |
|--------|-------|----------|----------|-----------|-------|
| `backend/` | 108 | 91 (84%) | 98 (91%) | 13,697 | FastAPI backend; large aggregate, not a good move candidate |
| `configs/` | 11 | 11 (100%) | 11 (100%) | 428 | **All files small; focused scope** |
| `docs/` | 347 | 231 (67%) | 279 (80%) | 59,164 | Documentation tree by design |
| `notebooks/` | 23 | 10 (43%) | 11 (48%) | 9,080 | Notebooks are standalone artifacts |
| `scripts/` | 59 | 37 (63%) | 47 (80%) | 11,288 | Heterogeneous utilities; moving piecemeal is more appropriate |
| `src/` | 68 | 36 (53%) | 47 (69%) | 14,685 | Main source; not a relocation target |
| `tests/` | 63 | 52 (83%) | 56 (89%) | 8,305 | Test files are expected to be small |
| `uqlab-flask/` | 18 | 15 (83%) | 17 (94%) | 1,768 | Self-contained Flask app; relocation would break its packaging |

`configs/` is the only root folder where 100% of files are below the 200 LoC threshold and whose contents have a single, well-defined responsibility.

## Selected candidate: `configs/`

### Current inventory

| LoC | File |
|-----|------|
| 26 | `configs/README.md` |
| 20 | `configs/experiment/fast_pilot.yaml` |
| 25 | `configs/test/test_dinov2_mlp.yaml` |
| 25 | `configs/test/test_resnet18_mcdropout.yaml` |
| 26 | `configs/test/test_cnn_mcdropout.yaml` |
| 40 | `configs/example_resnet18_mcdropout.yaml` |
| 44 | `configs/example_cnn_mcdropout.yaml` |
| 46 | `configs/experiment/default.yaml` |
| 48 | `configs/experiment/four_region.yaml` |
| 64 | `configs/experiment/four_region_cifar_resnet.yaml` |
| 64 | `configs/experiment/four_region_fashion_mlp.yaml` |

### Why it is a good candidate

1. **Small and uniform** — every file is under 200 LoC; the whole folder is only ~428 LoC.
2. **Single concern** — YAML experiment presets and smoke-test configs.
3. **Logical home exists** — the docs describe a `src/uqlab/shared/config/` package as the long-term home for configuration. The active implementation currently lives in `src/uqlab_core/shared/config/`, so `src/uqlab_core/configs/` is the natural destination.
4. **Mechanical move** — path references are centralized in `runtime_paths.configs_dir()` plus a few explicit strings in scripts and notebooks.
5. **Not a public API** — these are experiment presets, not imported code, so moving them does not change Python package semantics.

## Where `configs/` could go

| Option | Destination | Pros | Cons |
|--------|-------------|------|------|
| A | `src/uqlab_core/configs/` | Matches the active `uqlab_core` package; one source-of-truth location | Requires updating the package-specific `runtime_paths` helper |
| B | `src/uqlab/configs/` | Aligns with the documented MLOps structure | `src/uqlab/` is currently empty; would need to populate the package first |
| C | Keep at root, but split into `configs/experiment/` and `configs/test/` | Minimal churn | Does not reduce root clutter |

**Recommendation: Option A** — move to `src/uqlab_core/configs/` because that package is the one actually imported by the current scripts (`uqlab_core` is the real package behind the `uqlab` namespace references in docs and some scripts).

## What would need to change

Files that reference `configs/` explicitly:

1. `src/uqlab_core/runtime_paths.py` — update `configs_dir()` to return `repository_root() / "src" / "uqlab_core" / "configs"` (or resolve relative to the module path).
2. `scripts/runners/run_fast_uncertainty_classification.py` — default config path is built from `configs_dir()`, so it would follow automatically once `runtime_paths` is updated. Any hard-coded fallback strings should be removed.
3. `scripts/setup/validate_architectures.py` — uses `f"configs/test/{config_name}.yaml"`. Update to use `configs_dir()` from `uqlab_core.runtime_paths`.
4. `scripts/setup/generate_thesis_diagram.py` — verify whether it loads YAML from `configs/`; if so, switch to `configs_dir()`.
5. `src/uqlab_core/runner/notebook_run.py` — check for direct `configs/` paths and replace with `configs_dir()`.
6. Notebooks under `notebooks/` — several reference `configs/` in example paths. Update to use the runtime helper or document the new location.
7. Documentation — update `README.md`, `START_HERE.md`, `EXECUTION_FLOW_AND_CONFIG_GUIDE.md`, `docs/migration/HYDRA_GUIDE.md`, and the `configs/README.md` itself.
8. `pyproject.toml` / package manifests — if any package-data glob includes `configs/`, update it to `src/uqlab_core/configs/`.

No other root-level folder is as cleanly movable with so few touchpoints.

## Recommendation

1. Approve `configs/` as the single root-level small-file relocation candidate.
2. Prepare a follow-up branch that performs the move to `src/uqlab_core/configs/` and updates all references listed above.
3. Run the smoke-test suite (`scripts/setup/validate_architectures.py`) after the move to confirm YAML loading still works.
4. Update `docs/setup/CONFIG_AND_IMPORTS_STATUS.md` to reflect the new config location.

## Appendix: full candidate data

See the per-folder line counts in the table above. The next-best candidates (`uqlab-flask/` and `tests/`) are either self-contained apps or files that are expected to be small, so they are not recommended for relocation at this time.
