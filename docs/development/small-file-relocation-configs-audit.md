# Small-File Relocation Audit: `configs/`

## Status

✅ **Completed** — `configs/` has been relocated to `src/uqlab_core/configs/` on branch `cursor/small-file-relocation-candidates-6fd7`. The runtime path helper, package metadata, code references, notebooks, scripts, and documentation have been updated to use the new location.

## Summary

`configs/` was a small, root-level folder whose files were all under 200 lines of code. It was a good candidate for relocation into the `uqlab_core` package so that experiment presets ship with the library instead of living as a separate top-level directory.

## Size Check (original location)

Recursive line count for the `configs/` tree:

| File | Lines |
|------|-------|
| `configs/experiment/fast_pilot.yaml` | 19 |
| `configs/test/test_dinov2_mlp.yaml` | 25 |
| `configs/test/test_resnet18_mcdropout.yaml` | 25 |
| `configs/README.md` | 26 |
| `configs/test/test_cnn_mcdropout.yaml` | 26 |
| `configs/example_resnet18_mcdropout.yaml` | 40 |
| `configs/example_cnn_mcdropout.yaml` | 44 |
| `configs/experiment/default.yaml` | 45 |
| `configs/experiment/four_region.yaml` | 48 |
| `configs/experiment/four_region_cifar_resnet.yaml` | 64 |
| `configs/experiment/four_region_fashion_mlp.yaml` | 64 |
| **Total** | **426** |

All files are well below the 200–300 LoC threshold, making this folder a clean relocation candidate.

## Why It Can Be Moved

- `uqlab_core.runtime_paths.configs_dir()` already centralizes the lookup of the configs directory, so only one code path needs to change.
- The configs are tightly coupled to the `uqlab_core` package: they define `ExperimentConfig` shapes used by `uqlab_core.runner`, `uqlab_core.models`, and `uqlab_core.data`.
- `src/uqlab_core/configs/` is the conventional package-data location for YAML defaults shipped with the library.
- No tests hard-code the `configs/` path; only notebooks, scripts, and docs reference it, and those references can be updated mechanically.

## Proposed Move

```
before:
configs/
├── experiment/
├── test/
├── example_cnn_mcdropout.yaml
├── example_resnet18_mcdropout.yaml
└── README.md

after:
src/uqlab_core/configs/
├── experiment/
├── test/
├── example_cnn_mcdropout.yaml
├── example_resnet18_mcdropout.yaml
└── README.md
```

## Files Updated

1. ✅ `src/uqlab_core/runtime_paths.py` — `configs_dir()` now returns the package-local `configs/` directory.
2. ✅ `src/uqlab_core/pyproject.toml` — added `package-data` so YAML and README files are included when the package is installed.
3. ✅ `src/uqlab_core/shared/config/classification.py` — updated the default `--config` path and docstring references.
4. ✅ `src/uqlab_core/runner/notebook_run.py` — updated default four-region config paths.
5. ✅ `scripts/setup/validate_architectures.py` and `scripts/setup/generate_thesis_diagram.py` — updated hard-coded paths.
6. ✅ Notebooks under `notebooks/` — updated `configs/...` references.
7. ✅ Documentation under `docs/` and root-level markdown files — updated links and examples.
8. ✅ `configs/README.md` — moved to `src/uqlab_core/configs/README.md` and updated import examples.
9. ✅ Removed broken symlinks at the root (`uq_benchmarks`, `uq_classification`, `notebooks/validation/notebook_support`) that were pointing to obsolete `uqlab`/`walaris` paths and causing tooling errors.

## Risk Assessment

- **Low**: the runtime path helper is the single source of truth for config resolution.
- **Low**: no test files reference the `configs/` path directly.
- **Medium**: notebooks and documentation contain many `configs/...` strings that must be updated to keep examples runnable.

## Recommendation

Relocate `configs/` to `src/uqlab_core/configs/` and update the internal references listed above. This keeps small, library-owned config presets next to the code that consumes them and removes a root-level folder whose contents are all under the 200–300 LoC threshold.

**Result:** Completed as recommended above.
