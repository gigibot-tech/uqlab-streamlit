# Small File Relocation Candidates — `backend/` Root

> **Scope:** Examine the `backend/` root for files under 200/300 lines of code and relocate them to a more appropriate folder. This follows the same cleanup pattern as the broader [`ROOT_LEVEL_CLEANUP_ANALYSIS.md`](ROOT_LEVEL_CLEANUP_ANALYSIS.md).

---

## TL;DR

The `backend/` root contained **10 small executable/utility files** (all under 200 LoC) that were not core backend package files. They have been moved to `backend/scripts/`, which already housed the backend's small utility scripts (`entrypoint.sh`, `format.sh`, `lint.sh`, etc.).

| File | LoC | Old Location | New Location |
|------|-----|--------------|--------------|
| `start_backend.sh` | 17 | `backend/` | `backend/scripts/` |
| `start_backend_prod.sh` | 15 | `backend/` | `backend/scripts/` |
| `_python.sh` | 25 | `backend/` | `backend/scripts/` |
| `run_dev.py` | 32 | `backend/` | `backend/scripts/` |
| `run_prod.py` | 34 | `backend/` | `backend/scripts/` |
| `run_migration.py` | 45 | `backend/` | `backend/scripts/` |
| `run_benchmark_migration.py` | 59 | `backend/` | `backend/scripts/` |
| `run_method_type_migration.py` | 81 | `backend/` | `backend/scripts/` |
| `backfill_signals.py` | 84 | `backend/` | `backend/scripts/` |
| `fix_python314.sh` | 29 | `backend/` | `backend/scripts/` |

Files that **remain at `backend/` root** because they are required there:

| File | Reason |
|------|--------|
| `Dockerfile` | Must be at package root for Docker build context. |
| `pyproject.toml` | Backend package metadata. |
| `alembic.ini` | Alembic config, expected at package root. |
| `README.md` | Backend entry documentation. |
| `uv.lock` | Lockfile for the backend package. |
| `app/` | Core FastAPI application package. |
| `migrations/` | Alembic/SQL migrations. |

---

## Methodology

Line counts were measured with a Python helper counting non-empty lines. Only files under 200/300 LoC at the `backend/` root were considered. Config files, lockfiles, documentation, and the `app/` package were excluded because they belong at the backend root.

---

## Changes Made

### 1. Moved files to `backend/scripts/`

```bash
git mv backend/_python.sh backend/scripts/_python.sh
git mv backend/fix_python314.sh backend/scripts/fix_python314.sh
git mv backend/run_dev.py backend/scripts/run_dev.py
git mv backend/run_prod.py backend/scripts/run_prod.py
git mv backend/run_migration.py backend/scripts/run_migration.py
git mv backend/run_benchmark_migration.py backend/scripts/run_benchmark_migration.py
git mv backend/run_method_type_migration.py backend/scripts/run_method_type_migration.py
git mv backend/backfill_signals.py backend/scripts/backfill_signals.py
git mv backend/start_backend.sh backend/scripts/start_backend.sh
git mv backend/start_backend_prod.sh backend/scripts/start_backend_prod.sh
```

### 2. Updated internal path computations

Because the scripts now live in `backend/scripts/` instead of `backend/`, any code that computed paths from `Path(__file__).parent` had to be adjusted to `Path(__file__).parent.parent` so the backend directory is still resolved correctly.

Updated files:

- `backend/scripts/_python.sh` — now resolves `_BACKEND_DIR` from the script's grandparent directory.
- `backend/scripts/run_dev.py` — `BACKEND_DIR = Path(__file__).resolve().parent.parent`
- `backend/scripts/run_prod.py` — `BACKEND_DIR = Path(__file__).resolve().parent.parent`
- `backend/scripts/run_migration.py` — `backend_dir = Path(__file__).parent.parent`
- `backend/scripts/run_benchmark_migration.py` — `backend_dir = Path(__file__).parent.parent`
- `backend/scripts/run_method_type_migration.py` — `backend_dir = Path(__file__).parent.parent`
- `backend/scripts/backfill_signals.py` — `backend_dir = Path(__file__).parent.parent`
- `backend/scripts/fix_python314.sh` — changed `cd "$(dirname "$0")/backend"` to `cd "$(dirname "$0")/.."`
- `backend/scripts/start_backend.sh` — updated `PYTHONPATH` echo and usage comments.
- `backend/scripts/start_backend_prod.sh` — updated `PYTHONPATH` echo and usage comments.

### 3. Updated references

All documentation and in-code references to the moved files were updated:

- `backend/BACKEND_MODES.md`
- `backend/BACKFILL_README.md`
- `backend/migrations/README.md`
- `backend/app/core/ml_bootstrap.py`
- `docs/user-guides/BACKEND_STARTUP_GUIDE.md`
- `docs/phases/PHASE4_DATABASE_SCHEMA.md`
- `docs/features/checkpoint-arsenal.md`
- `docs/development/BACKEND_FIX_SUMMARY.md`
- `docs/development/INFINITE_RERUN_TROUBLESHOOTING.md`
- `docs/development/RERUN_FIX_VERIFICATION.md`
- `docs/development/RESNET_FEATURE_EXTRACTOR_FIX.md`
- `scripts/maintenance/quick_test.sh`

### 4. Files kept at `backend/` root

- `Dockerfile`, `pyproject.toml`, `alembic.ini`, `README.md`, `uv.lock` — required by tooling or convention.
- `app/`, `migrations/` — core package structure.
- Architecture/docs (`API_ENDPOINTS_EXPLAINED.md`, `BACKEND_MODES.md`, `BACKFILL_README.md`, `RUN_LABEL_NOISE_SWEEP_FLOW.md`, `STORAGE_ARCHITECTURE.md`) — left at root as backend documentation.

---

## New `backend/` Layout

```
backend/
├── app/                       # FastAPI application
├── migrations/                # Alembic/SQL migrations
├── scripts/                   # Utility & startup scripts (NEW home)
│   ├── _python.sh
│   ├── backfill_signals.py
│   ├── entrypoint.sh
│   ├── fix_python314.sh
│   ├── format.sh
│   ├── lint.sh
│   ├── prestart.sh
│   ├── run_benchmark_migration.py
│   ├── run_dev.py
│   ├── run_method_type_migration.py
│   ├── run_migration.py
│   ├── run_prod.py
│   ├── start_backend.sh
│   ├── start_backend_prod.sh
│   ├── test.sh
│   └── tests-start.sh
├── Dockerfile
├── alembic.ini
├── pyproject.toml
├── README.md
└── uv.lock
```

---

## Usage After Move

From the repository root:

```bash
# Development mode
./backend/scripts/start_backend.sh

# Production mode (use while experiments are running)
./backend/scripts/start_backend_prod.sh

# Database migrations
python3 backend/scripts/run_migration.py
python3 backend/scripts/run_benchmark_migration.py
python3 backend/scripts/run_method_type_migration.py

# Backfill signals
python backend/scripts/backfill_signals.py
```

From the `backend/` directory:

```bash
./scripts/start_backend.sh
./scripts/start_backend_prod.sh
python3 scripts/run_migration.py
```

---

## Validation

- `python3 -m py_compile` passed for all moved Python scripts.
- `bash -n` passed for all moved shell scripts.
- `backend/` root no longer contains the relocated small files.
- All non-generated references to the old paths were updated.
- `dependencies.json` (a generated artifact) still contains stale paths and can be regenerated if needed.

---

## Related Documents

- [`ROOT_LEVEL_CLEANUP_ANALYSIS.md`](ROOT_LEVEL_CLEANUP_ANALYSIS.md) — Broader root-cleanup proposal.
- [`backend/BACKEND_MODES.md`](../../backend/BACKEND_MODES.md) — Backend development vs. production mode.
- [`backend/BACKFILL_README.md`](../../backend/BACKFILL_README.md) — Signal backfill instructions.
