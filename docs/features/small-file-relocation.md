# Small File Relocation Candidates

> **Trigger**: cron maintenance check — find a root-level folder whose files are all smaller than 200/300 LoC and decide whether it can be relocated into a package.

## Principle

A root-level folder that contains only tiny files is usually a “miscellaneous” bucket.  If every file fits under a small LoC threshold, the folder is a candidate for relocation into a package that actually owns the content (e.g. `src/uqlab_core/configs` or `backend/app/configs`).

## How to reproduce the scan

```bash
python3 scripts/maintenance/detect_small_file_relocation_candidates.py
```

The scanner walks each immediate root directory, ignores binary/lock/cache artifacts, and reports any folder whose **maximum** file size is below 200 LoC and/or 300 LoC.

## Current scan result

| Root Folder | Files | Max LoC | Thresholds Met | Proposed Home |
|-------------|-------|---------|----------------|---------------|
| configs     | 11    | 64      | 200, 300       | `src/uqlab_core/configs` (package data) or `backend/app/configs` |

Only `configs/` qualifies today. Every YAML and its README is well below 200 lines.

### `configs/` file inventory

| File | LoC |
|------|-----|
| experiment/fast_pilot.yaml | 20 |
| test/test_dinov2_mlp.yaml | 25 |
| test/test_resnet18_mcdropout.yaml | 25 |
| README.md | 26 |
| test/test_cnn_mcdropout.yaml | 26 |
| example_resnet18_mcdropout.yaml | 40 |
| example_cnn_mcdropout.yaml | 44 |
| experiment/default.yaml | 46 |
| experiment/four_region.yaml | 48 |
| experiment/four_region_cifar_resnet.yaml | 64 |
| experiment/four_region_fashion_mlp.yaml | 64 |

## Why `configs/` is a relocation candidate

The configs are currently loaded from the repository root:

```26:28:src/uqlab_core/runtime_paths.py
    def configs_dir() -> Path:
        """Experiment YAML configs (``configs/experiment``, ``configs/test``, …)."""
        return repository_root() / "configs"
```

Because they live at the root, they are not shipped with the `uqlab_core` package. Moving them into `src/uqlab_core/configs` would make them true package data and keep the repository root free of small content buckets.

## Files that reference the current `configs/` path

A relocation would need to update these hard-coded paths:

```11:11:scripts/setup/validate_architectures.py
    config_path = f"configs/test/{config_name}.yaml"
```

```12:12:scripts/setup/generate_thesis_diagram.py
    --config configs/experiment/default.yaml \\
```

```86:91:src/uqlab_core/runner/notebook_run.py
            "config_path": root / "configs/experiment/four_region_fashion_mlp.yaml",
```

```26:26:configs/README.md
configs/
```

Additionally, `src/uqlab_core/pyproject.toml` would need `package-data` so the YAML files are included in the wheel, and `src/uqlab_core/runtime_paths.py` would change to package-relative resolution.

## Proposed destination options

| Option | Path | Pros | Cons |
|--------|------|------|------|
| **A** | `src/uqlab_core/configs` | Shipped with `uqlab_core`; no root clutter; matches `runtime_paths` purpose | Needs `package-data` in `src/uqlab_core/pyproject.toml` |
| **B** | `backend/app/configs` | Keeps presets close to the FastAPI backend | Notebooks and CLI also need them, so cross-package imports increase |
| **C** | Keep at root | No churn | Fails the “small files belong in a package” principle |

**Recommendation**: Option A — move the configs into `src/uqlab_core/configs` as package data, because they are consumed by the core library, notebooks, and the CLI, not exclusively by the backend.

## Notes on other root folders

- `data/` only contains a `.gitkeep`. It can remain the runtime data root (see `UQLAB_DATA_DIR`), but the `.gitkeep` is not a relocation candidate.
- `uqlab-flask/`, `backend/`, `scripts/`, `src/`, `tests/`, `docs/`, and `notebooks/` all contain files larger than 300 LoC, so they do not qualify as “all small files”.

## Decision required before moving

1. Choose the destination package (recommended: `src/uqlab_core/configs`).
2. Update `runtime_paths.configs_dir()` to resolve package-relative.
3. Update hard-coded `configs/...` paths in scripts and notebooks.
4. Add `package-data` to `src/uqlab_core/pyproject.toml`.
5. Run `validate_architectures.py` and the four-region notebook to confirm paths still work.
