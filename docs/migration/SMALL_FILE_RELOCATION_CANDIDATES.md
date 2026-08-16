# Small File Relocation Candidates

Quick scan of root-level folders to find one whose contents are well under 200/300 LoC and assess whether relocation makes sense.

## Candidate root folder: `configs/`

`configs/` is the only root-level folder whose files are all small enough to be a relocation candidate:

| File | LoC |
|------|-----|
| `configs/experiment/fast_pilot.yaml` | 19 |
| `configs/test/test_dinov2_mlp.yaml` | 25 |
| `configs/test/test_resnet18_mcdropout.yaml` | 25 |
| `configs/test/test_cnn_mcdropout.yaml` | 26 |
| `configs/README.md` | 26 |
| `configs/example_resnet18_mcdropout.yaml` | 40 |
| `configs/example_cnn_mcdropout.yaml` | 44 |
| `configs/experiment/default.yaml` | 45 |
| `configs/experiment/four_region.yaml` | 48 |
| `configs/experiment/four_region_cifar_resnet.yaml` | 64 |
| `configs/experiment/four_region_fashion_mlp.yaml` | 64 |
| **Total** | **426** |

All files are under 100 LoC, and the entire folder is only 426 LoC.

### What it is used for

- Experiment YAML presets loaded by `run_fast_uncertainty_classification.py` and the validation runners.
- Test/architecture smoke configs used by `scripts/setup/validate_architectures.py`.
- Referenced in several notebooks and in `src/uqlab_core/runtime_paths.py` via `configs_dir()`.
- Documented in `docs/setup/CONFIG_AND_IMPORTS_STATUS.md` and `docs/setup/MIGRATION_TO_NESTED_CONFIG.md`.

### Can it be moved somewhere?

Technically yes, but with a few caveats.

The runtime path is already centralized in `src/uqlab_core/runtime_paths.py`:

```python
def configs_dir() -> Path:
    """Experiment YAML configs (``configs/experiment``, ``configs/test``, …)."""
    return repository_root() / "configs"
```

That means moving the folder only requires updating `configs_dir()` to keep most Python consumers working. However, there are also direct string references scattered across docs, notebooks, scripts, and `START_HERE.md` (e.g., `configs/experiment/four_region.yaml`). Those would need to be updated as well.

### Where could it go?

| Option | Destination | Notes |
|--------|-------------|-------|
| Keep as-is | `configs/` | Least churn. Short-term legacy home for YAML configs. |
| Move under package | `src/uqlab_core/configs/` | Keeps config assets with the package. Requires updating `configs_dir()` and every direct path. |
| Merge with Python configs | `src/uqlab_core/shared/config/` | Aligns with the long-term direction to replace YAML with Python/Pydantic config classes. |

### Recommendation

Do **not** perform a simple folder relocation of `configs/`.

The existing architecture docs already treat the YAML files as **short-term legacy** and recommend migrating to Python config classes in `src/uqlab_core/shared/config/` (see `docs/setup/CONFIG_AND_IMPORTS_STATUS.md` and `docs/setup/MIGRATION_TO_NESTED_CONFIG.md`). Moving the YAML folder first would create churn twice: once to relocate, and again to migrate the content to Python.

Instead, the preferred path is:

1. Keep `configs/` where it is for now.
2. Convert the YAML presets into Python config factories or Pydantic defaults under `src/uqlab_core/shared/config/`.
3. Once the YAML files are no longer the source of truth, remove `configs/` and update `configs_dir()` to point to the new location or retire it.

If a physical relocation is required before the Python migration, `src/uqlab_core/configs/` is the most natural destination, but it still requires touching every consumer listed above.

## Other folders considered

- `data/` — only contains an empty `.gitkeep`. It is a placeholder for runtime data, not a relocation candidate.
- `uqlab-flask/` — contains a 652-line executor and a CSS file, so it is not uniformly under the 200/300 LoC threshold.
- `notebooks/`, `scripts/`, `tests/`, `backend/`, `docs/`, `src/` — all contain files well above 300 LoC.
