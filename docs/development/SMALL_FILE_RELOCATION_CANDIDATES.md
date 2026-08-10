# Small-File Root-Folder Relocation Candidates

## Question

Find a root-level folder whose files are all < 200/300 LoC and determine whether they can be moved somewhere else.

## Candidate: `configs/`

All files in the `configs/` root folder are well under the 200/300 line threshold:

| File | LoC |
|---|---|
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

No other root-level folder has all its files consistently this small. (`data/` is essentially empty except for `.gitkeep`, and folders like `tests/`, `scripts/`, `src/`, and `backend/` contain many larger files.)

## Can it be moved?

Technically yes, but **not recommended** right now.

- `configs/` is the canonical location documented in `configs/README.md`, `docs/setup/CONFIG_AND_IMPORTS_STATUS.md`, and `docs/development/ROOT_LEVEL_CLEANUP_ANALYSIS.md`.
- `src/uqlab_core/runtime_paths.py::configs_dir()` points to the repository root `configs/` directory, and many scripts, notebooks, and tests reference it.
- The current migration status explicitly states: **"Short term: Keep using YAML configs in `configs/`"**.
- The files are small because YAML experiment presets are naturally concise; their size is not a code-smell.

## Verdict

Keep `configs/` at the repository root. It is already the correct home for YAML experiment presets, and relocation would create churn without clear architectural benefit.
