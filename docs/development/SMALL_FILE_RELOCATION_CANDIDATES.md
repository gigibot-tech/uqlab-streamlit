# Small Root-Folder Relocation Candidate Audit

**Generated:** 2026-08-09  
**Branch:** `cursor/small-file-relocation-candidates-0946`  
**Scan thresholds:** 200 LoC and 300 LoC (text files only)

---

## Purpose

Identify root-level folders where every file is small enough (≤ 200/300 lines) that the folder could potentially be relocated to a more appropriate place. This audit does **not** move files; it records candidates and the constraints that keep them at root.

The reusable scanner lives at `scripts/maintenance/find_small_root_folders.py`.

---

## Methodology

1. Walk every directory immediately under the repo root (`/`).
2. Count lines in each text file, skipping binary files (images, PDFs, lock files, compiled artifacts, archives).
3. For each folder, report `max` and `total` LoC and whether every file is under the threshold.
4. Apply project conventions to decide whether a folder is a true relocation candidate.

---

## Scan results (root folders)

| Folder            | Files | Max LoC | Total LoC | All ≤ 200 | All ≤ 300 | Relocation note |
|-------------------|-------|---------|-----------|-----------|-----------|-----------------|
| `.bob`            | 3     | 663     | 1,620     | No        | No        | Tooling; keep at root |
| `.cursor`         | 1     | 72      | 72        | Yes       | Yes       | Tooling; keep at root |
| `.docs`           | 5     | 252     | 560       | No        | Yes       | Private docs; keep at root |
| `.vscode`         | 3     | 31      | 68        | Yes       | Yes       | IDE settings; keep at root |
| `backend`         | 112   | 1,393   | 12,244    | No        | No        | Large; keep at root |
| `configs`         | 11    | 64      | 428       | Yes       | Yes       | **Candidate** — see below |
| `data`            | 1     | 0       | 0         | Yes       | Yes       | Runtime data dir; keep at root |
| `docs`            | 348   | 1,224   | 59,297    | No        | No        | Large; keep at root |
| `notebooks`       | 23    | 1,257   | 9,080     | No        | No        | Large; keep at root |
| `scripts`         | 60    | 652     | 11,463    | No        | No        | Large; keep at root |
| `src`             | 68    | 923     | 14,685    | No        | No        | Large; keep at root |
| `tests`           | 63    | 473     | 8305      | No        | No        | Above threshold; keep at root |
| `uqlab-flask`     | 18    | 652     | 1,768     | No        | No        | Above threshold; keep at root |

---

## Candidate analysis

### `configs/` (11 files, max 64 LoC, total 428 LoC)

This is the only root folder whose **functional** files are all well below both thresholds. It is a natural relocation candidate.

**What it contains:**

```text
configs/
├── experiment/          # YAML presets
│   ├── default.yaml
│   ├── fast_pilot.yaml
│   ├── four_region.yaml
│   ├── four_region_cifar_resnet.yaml
│   └── four_region_fashion_mlp.yaml
├── test/                # Smoke-test configs
├── example_cnn_mcdropout.yaml
├── example_resnet18_mcdropout.yaml
└── README.md
```

**Could it move?** Yes — to `src/uqlab_core/configs/`. This has been done in prior branches and is consistent with the current `src/uqlab_core/` package structure.

**What would need to change if it moves:**

| File / area | Current reference | Required update |
|-------------|-------------------|-----------------|
| `src/uqlab_core/runtime_paths.py` | `configs_dir() -> repository_root() / "configs"` | Point to `repository_root() / "src" / "uqlab_core" / "configs"` (or compute package-relative path) |
| `src/uqlab_core/runner/notebook_run.py` | `root / "configs/experiment/..."` | Use `configs_dir()` from `runtime_paths` |
| `src/uqlab_core/shared/config/classification.py` | `default="configs/fast_uq_classification.yaml"` | Update default or remove if the file no longer exists |
| `configs/README.md` | Mentions `configs/` paths | Rewrite for new location |
| `START_HERE.md`, `README.md`, `EXECUTION_FLOW_AND_CONFIG_GUIDE.md` | `--config configs/...` examples | Update examples |
| `docs/migration/HYDRA_GUIDE.md`, `MIGRATION_GUIDE.md`, `docs/setup/CONFIG_AND_IMPORTS_STATUS.md` | `configs/` references | Update references |
| `scripts/setup/validate_architectures.py`, `generate_thesis_diagram.py` | Hard-coded `configs/` paths | Update or use `configs_dir()` |

Because `runtime_paths.configs_dir()` is the central abstraction, the actual code impact is small: update the helper and replace the few hard-coded paths with the helper. The larger churn is documentation.

**Why it might stay at root:**

- `docs/development/ROOT_LEVEL_CLEANUP_ANALYSIS.md` lists `configs/` under "Final Root Level Structure" as a folder that should remain at root.
- YAML configs are frequently referenced by CLI examples and external notebooks; keeping them at root makes the paths shorter and easier to discover.
- The folder is small enough that it does not meaningfully clutter the root.

**Verdict:** `configs/` is the sole actionable candidate, but moving it is a trade-off. Keep it at root unless the team is actively normalizing `src/uqlab_core/` as the single location for all runtime assets.

### `data/` (1 file, 0 LoC)

Contains only `data/.gitkeep`. This is intentionally an empty runtime data directory. Do not relocate.

---

## Tooling folders that stay at root

The following folders are small but are standard repo-root tooling:

- `.cursor/` — Cursor skills / agent context
- `.vscode/` — Editor settings
- `.docs/` — Private project docs (kept separate from `docs/`)
- `.bob/` — Bob tooling (exceeds 300 LoC anyway)

These should not be relocated.

---

## Recommendation

1. **No immediate relocation is required.** The root is not cluttered by small folders.
2. **If the team wants to relocate one folder, `configs/` is the only viable target.** Move it to `src/uqlab_core/configs/` and update the references listed above.
3. **Re-run the scanner** before future relocation passes:

```bash
python scripts/maintenance/find_small_root_folders.py
python scripts/maintenance/find_small_root_folders.py --threshold 200
```

---

## Related documents

- `docs/development/ROOT_LEVEL_CLEANUP_ANALYSIS.md` — prior root-cleanup plan (keeps `configs/` at root)
- `docs/development/FILE_ORGANIZATION_ANALYSIS.md` — separation-of-concerns analysis
- `docs/development/PYTHON_FILES_INVENTORY.md` — package inventory
- `PACKAGE_REORGANIZATION_PROPOSAL.md` — proposed `src/` layout

---

**Status:** Audit complete; no files moved.
