# Small-File Relocation Candidates — 1130

This report documents the small-file relocation pass for the `configs/` root
folder.  All files in `configs/` are below the 300 non-empty-LoC threshold, and
several of them were loose or located next to unrelated consumers.

## Findings

`configs/` was the only root-level directory where every countable file was
<= 300 non-empty LoC:

| File | LoC |
|------|-----|
| `configs/experiment/fast_pilot.yaml` | 15 |
| `configs/README.md` | 22 |
| `configs/examples/example_resnet18_mcdropout.yaml` | 32 |
| `configs/examples/example_cnn_mcdropout.yaml` | 35 |
| `configs/experiment/default.yaml` | 38 |
| `configs/experiment/four_region.yaml` | 42 |
| `configs/experiment/four_region_cifar_resnet.yaml` | 58 |
| `configs/experiment/four_region_fashion_mlp.yaml` | 58 |

## Actions Taken

### 1. Grouped loose architecture examples

Two example YAMLs lived directly under `configs/` and were only referenced by
documentation.  They are now grouped under `configs/examples/`:

- `configs/example_cnn_mcdropout.yaml` → `configs/examples/example_cnn_mcdropout.yaml`
- `configs/example_resnet18_mcdropout.yaml` → `configs/examples/example_resnet18_mcdropout.yaml`

### 2. Moved test configs next to their consumer

The architecture smoke configs were stored in `configs/test/` but consumed only
by `scripts/setup/validate_architectures.py`.  They have been relocated to
`scripts/setup/configs/`:

- `configs/test/test_cnn_mcdropout.yaml` → `scripts/setup/configs/test_cnn_mcdropout.yaml`
- `configs/test/test_dinov2_mlp.yaml` → `scripts/setup/configs/test_dinov2_mlp.yaml`
- `configs/test/test_resnet18_mcdropout.yaml` → `scripts/setup/configs/test_resnet18_mcdropout.yaml`

The empty `configs/test/` directory was removed.

## Updated Consumers

- `scripts/setup/validate_architectures.py` now loads configs from
  `scripts/setup/configs/{name}.yaml`.
- `configs/README.md` reflects the new layout.
- `docs/setup/CONFIG_AND_IMPORTS_STATUS.md` updated.
- `docs/phases/PHASE7_1_ARCHITECTURE_SELECTOR.md` updated.
- `docs/migration/MIGRATION_GUIDE.md` updated.

## Tooling

Added `scripts/maintenance/find_small_file_relocation_candidates.py` to
automate future scans of root-level folders for small-file relocation
candidates.

## Result

`configs/` remains a conventional top-level config store, but is now limited
to primary experiment presets and grouped examples.  Test/validation configs live
next to the script that uses them.
