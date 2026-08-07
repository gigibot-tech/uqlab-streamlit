# Small Root-Folder Relocation Analysis

## Task

Scan the non-hidden top-level directories for a folder whose files are all under 200–300 lines of code and evaluate whether it can be relocated.

## Method

All non-hidden root folders were scanned and line counts were computed for every file:

```bash
for d in backend configs data docs notebooks scripts src tests uqlab-flask; do
  find "$d" -type f -not -path '*/.*' -exec wc -l {} \;
done
```

## Results

| Folder | Total files | Files < 200 LoC | Files < 300 LoC | Max file | Qualifies |
|--------|-------------|-----------------|-----------------|----------|-----------|
| `backend/` | 114 | 97 | 104 | 1482 | ❌ |
| `configs/` | 11 | 11 | 11 | 64 | ✅ |
| `data/` | 1 | 1 | 1 | 0 | ✅ (trivial) |
| `docs/` | 347 | 231 | 279 | 1223 | ❌ |
| `notebooks/` | 23 | 10 | 11 | 1257 | ❌ |
| `scripts/` | 60 | 37 | 47 | 652 | ❌ |
| `src/` | 69 | 37 | 48 | 923 | ❌ |
| `tests/` | 63 | 52 | 56 | 473 | ❌ |
| `uqlab-flask/` | 18 | 15 | 17 | 652 | ❌ |

`configs/` is the only meaningful root folder where every file is under 200 LoC (maximum 64 lines).

## Contents of `configs/`

```
configs/
├── README.md                           26 LoC
├── example_cnn_mcdropout.yaml          44 LoC
├── example_resnet18_mcdropout.yaml     40 LoC
├── experiment/
│   ├── default.yaml                    45 LoC
│   ├── fast_pilot.yaml                 19 LoC
│   ├── four_region.yaml                48 LoC
│   ├── four_region_cifar_resnet.yaml   64 LoC
│   └── four_region_fashion_mlp.yaml    64 LoC
└── test/
    ├── test_cnn_mcdropout.yaml         26 LoC
    ├── test_dinov2_mlp.yaml            25 LoC
    └── test_resnet18_mcdropout.yaml    25 LoC
```

## Relocation decision

`configs/` **can be moved** into the package that owns it, because:

1. Every file is small (< 200 LoC) and self-contained.
2. The files are YAML experiment presets consumed by `uqlab_core` code (`ExperimentConfig.from_yaml`, `runtime_paths.configs_dir()`, `notebook_run.default_four_region_runs`).
3. Shipping them inside `src/uqlab_core/configs/` lets them travel with the installed package instead of relying on a root directory that may not exist at runtime.
4. No runtime data lives in `configs/`; it is purely static configuration.

### Target location

```
configs/ → src/uqlab_core/configs/
```

### Changes made

- Moved `configs/` → `src/uqlab_core/configs/`.
- Updated `src/uqlab_core/runtime_paths.py` so `configs_dir()` resolves relative to the package.
- Updated `src/uqlab_core/shared/config/classification.py` to use the package config directory for the default `--config` path and updated the merge docstring.
- Updated `src/uqlab_core/runner/notebook_run.py` so `default_four_region_runs()` uses `configs_dir()` instead of `root / "configs"`.
- Added `package-data` in `src/uqlab_core/pyproject.toml` so the YAML files are included in the installed wheel.
- Updated all documentation and scripts that referenced `configs/` (README, START_HERE, execution guide, migration guides, feature docs, notebooks, and validation scripts).
- Updated `src/uqlab_core/configs/README.md` to describe the new package location and `uqlab_core` imports.

### Why this is safe

- `runtime_paths.configs_dir()` is the single source of truth for config resolution; updating it fixes all consumers.
- All in-tree references were updated to `src/uqlab_core/configs/` or to use `configs_dir()`.
- The YAML files are now packaged data, so they remain accessible after `pip install uqlab-core`.

## Remaining root folders

- `data/` only contains a `.gitkeep` placeholder; it stays at the root because it is the runtime data directory referenced by `runtime_paths.data_root()`.
- All other root folders contain files larger than 300 LoC and are intentionally kept at the root level for their respective concerns (backend, docs, notebooks, scripts, source, tests, legacy Flask UI).
