# Small-File Relocation Analysis

Generated as part of the `cursor/small-file-relocation-candidates-*` branch review.

## Criteria

- **Strict small**: <= 200 LoC
- **Lenient small**: <= 300 LoC
- Focus is on top-level directories (root folders) whose contents are all small.

## Root folder inspected: `configs/`

The `configs/` directory is the only root-level folder whose contents are **all** under the 200 LoC threshold:

| File | LoC | Note |
|------|-----|------|
| `configs/experiment/fast_pilot.yaml` | 19 | CLI default |
| `configs/test/test_cnn_mcdropout.yaml` | 26 | Smoke config |
| `configs/test/test_dinov2_mlp.yaml` | 25 | Smoke config |
| `configs/test/test_resnet18_mcdropout.yaml` | 25 | Smoke config |
| `configs/README.md` | 26 | Folder documentation |
| `configs/example_resnet18_mcdropout.yaml` | 40 | Example config |
| `configs/example_cnn_mcdropout.yaml` | 44 | Example config |
| `configs/experiment/default.yaml` | 45 | Default preset |
| `configs/experiment/four_region.yaml` | 48 | Four-region preset |
| `configs/experiment/four_region_cifar_resnet.yaml` | 64 | Four-region preset |
| `configs/experiment/four_region_fashion_mlp.yaml` | 64 | Four-region preset |
| **Total** | **426** | Across 11 files |

## Can `configs/` be moved?

**Recommendation: keep `configs/` at the repository root.**

Reasons:

1. **Conventional location** — YAML experiment presets are typically stored at the project root so CLI tools, notebooks, and documentation can reference them without knowing the internal package layout.
2. **Runtime path dependency** — `uqlab.runtime_paths.configs_dir()` resolves to the root `configs/` directory. `ExperimentConfig.from_yaml(configs_dir() / "experiment" / "four_region.yaml")` and similar calls are used throughout the codebase and notebooks.
3. **Documentation references** — `configs/README.md`, `docs/setup/CONFIG_AND_IMPORTS_STATUS.md`, and several notebooks document the root-level `configs/` path.
4. **No natural package home** — The configs are consumed by both the ML core (`src/uqlab_core/`) and the orchestrator (`src/uqlab_orchestrator/`), so placing them inside either package would create an awkward cross-package dependency. They are project-level assets, not source code.

## Other small root-level files (separate from the folder review)

While inspecting the root, the following individual files also satisfy the small-file threshold and are better scoped under `scripts/`:

| File | LoC | Suggested target |
|------|-----|------------------|
| `organize_root_scripts.sh` | 57 | `scripts/maintenance/` |
| `start.sh` | 61 | `scripts/deployment/` |
| `analyze_md_files.py` | 63 | `scripts/analysis/` |
| `start-with-minio.sh` | 88 | `scripts/deployment/` |

These were relocated in this branch; see the commit history for details.

## Summary

- **Root folder with all small files**: `configs/`
- **Move `configs/`?** No — keep it at the repository root.
- **Additional action taken**: Relocated four small root-level scripts to appropriate `scripts/` subdirectories.
