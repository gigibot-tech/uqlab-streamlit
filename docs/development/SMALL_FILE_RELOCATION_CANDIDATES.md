# Small-File Root-Folder Relocation Candidates

**Goal:** Find a top-level folder whose files are all under ~200–300 lines of code and assess whether the whole folder can be relocated elsewhere in the repo.

**Scope:** Root-level directories only (`configs`, `data`, `docs`, `scripts`, `src`, `tests`, `backend`, `notebooks`, `uqlab-flask`).

---

## Methodology

Line counts were measured with `wc -l`. The threshold used for this scan is **300 LoC**; the 200 LoC boundary is also noted where it changes the candidate set.

| Root folder | Total files | Files ≤ 300 LoC | Files > 300 LoC | All files ≤ 300? |
|-------------|------------:|----------------:|----------------:|:----------------:|
| `configs`   | 11         | 11 (100%)       | 0               | **Yes**          |
| `data`      | 1          | 1 (100%)        | 0               | Yes (only `.gitkeep`) |
| `docs`      | 347        | 280 (80%)       | 67              | No               |
| `scripts`   | 60         | 48 (80%)        | 12              | No               |
| `src`         | 69         | 49 (71%)        | 20              | No               |
| `tests`       | 63         | 56 (88%)        | 7               | No               |
| `backend`     | 114        | 105 (92%)       | 9               | No               |
| `notebooks`   | 23         | 11 (47%)        | 12              | No               |
| `uqlab-flask` | 18         | 17 (94%)        | 1               | No               |

Only two folders have **every** file under the 300 LoC threshold:

1. `configs/` — the only folder with meaningful, multi-file content.
2. `data/` — contains only `data/.gitkeep` (0 LoC), so it is trivially small but not a useful relocation target.

At the stricter **200 LoC** threshold, `configs/` still qualifies (max file is 64 LoC). No other meaningful root folder has all files under 200 LoC.

---

## Candidate: `configs/`

### Current contents

```
configs/
├── README.md                              26
├── example_cnn_mcdropout.yaml             44
├── example_resnet18_mcdropout.yaml        40
├── experiment/
│   ├── default.yaml                       46
│   ├── fast_pilot.yaml                    20
│   ├── four_region.yaml                   48
│   ├── four_region_cifar_resnet.yaml      64
│   └── four_region_fashion_mlp.yaml       64
└── test/
    ├── test_cnn_mcdropout.yaml            26
    ├── test_dinov2_mlp.yaml               25
    └── test_resnet18_mcdropout.yaml       25
```

**All 11 files are ≤ 64 LoC**, well below the 200/300 LoC thresholds.

### Where it is referenced

| Reference | Location |
|-----------|----------|
| Central path resolver | `src/uqlab_core/runtime_paths.py` (`configs_dir() -> repository_root() / "configs"`) |
| CLI runner | `src/uqlab_core/runner/notebook_run.py` hard-codes `root / "configs/experiment/..."` |
| Architecture validation | `scripts/setup/validate_architectures.py` uses `f"configs/test/{config_name}.yaml"` |
| Docs / Hydra guide | `docs/migration/HYDRA_GUIDE.md`, `docs/migration/MIGRATION_GUIDE.md`, `README.md`, `START_HERE.md`, etc. |

### Relocation options

#### Option A — Move to `src/uqlab_core/configs/`

- **Pros:** Configs live next to the package that consumes them; root becomes slimmer.
- **Cons:**
  - YAML files are not Python source; mixing them into `src/uqlab_core/` is unconventional for a Python project.
  - Hydra examples and many scripts reference `configs/` relative to the repo root; moving the folder would force updates to every `config_path` and every documentation example.
  - `runtime_paths.configs_dir()` currently resolves to `repository_root() / "configs"`; moving it means either changing the central resolver or adding a special case for installed vs. editable installs.

#### Option B — Keep at repository root

- **Pros:**
  - Standard Python project layout for experiment/config files.
  - No import or documentation changes required.
  - Existing `docs/development/ROOT_LEVEL_CLEANUP_ANALYSIS.md` explicitly lists `configs/` as a **KEEP** item at the root level.
- **Cons:** Adds one more top-level directory (minor clutter).

### Verdict for `configs/`

**Do not relocate.** `configs/` is the only root folder that fully meets the small-file criterion, but it is intentionally a root-level configuration directory. Moving it would create more churn (path updates, doc updates, Hydra examples) than value, and it contradicts the existing root-cleanup plan.

---

## Honorable mention: `data/`

- Only contains `data/.gitkeep` (0 LoC).
- `src/uqlab_core/runtime_paths.py` resolves `data_root()` to `_REPO_ROOT / "data"` when `UQLAB_DATA_DIR` is unset.
- **Verdict:** Keep. The directory is a runtime data root, not content that can be relocated.

---

## Summary

- **Folder that satisfies the < 200/300 LoC criterion:** `configs/` (max 64 LoC per file).
- **Can it be moved somewhere?** Technically yes, e.g. to `src/uqlab_core/configs/`, but it is not recommended.
- **Recommended action:** Leave `configs/` at the repository root. The small file sizes are a feature (focused YAML experiment configs), not a signal that the folder should be relocated.
