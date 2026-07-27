# Small File Relocation Candidates — Root Folder Audit

This audit checks the repository root for code files under **200/300 LoC** and identifies whether they can be relocated to a more appropriate subdirectory.

## Analyzed folder

Repository root (`/`)

## Thresholds

- **< 200 LoC**: strong relocation candidate when the file is a standalone utility.
- **< 300 LoC**: still small, but kept at root if it is a documented entry-point or conventionally root-level file.

## Root-level code files found

| File | LoC | Threshold | Entry-point / documented | Relocation action |
|------|-----|-----------|--------------------------|-------------------|
| `docker-compose.yml` | 40 | < 200 | Yes (conventional root file) | **Kept at root** |
| `start.sh` | 47 | < 200 | Yes (commented in `streamlit_requirements.txt`) | **Kept at root** |
| `start-with-minio.sh` | 69 | < 200 | Yes (`docs/setup/minio.md`, `docs/architecture/minio-storage.md`) | **Kept at root** |
| `organize_root_scripts.sh` | 48 | < 200 | No | **Moved to `scripts/maintenance/organize_root_scripts.sh`** |
| `analyze_md_files.py` | 53 | < 200 | No | **Moved to `scripts/analysis/analyze_md_files.py`** |
| `streamlit_app_progressive.py` | 328 | — | Yes (Streamlit entry point) | **Kept at root** |

## Files moved

### `organize_root_scripts.sh` → `scripts/maintenance/`

- Purpose: move stray root-level scripts into `scripts/`, `tests/`, etc.
- Change: added `cd "$(dirname "$0")/../.."` so it still runs from the repo root regardless of invocation path.
- No other references found in the repo.

### `analyze_md_files.py` → `scripts/analysis/`

- Purpose: categorize markdown files in the repo root by keyword.
- Change: replaced `os.listdir('.')` with `Path(__file__).resolve().parents[2]` so it always scans the repo root.
- Updated `scripts/analysis/README.md` to document the new location.
- No other references found in the repo.

## Files kept at root and why

- `docker-compose.yml`: Docker Compose conventionally lives at the repository root.
- `start.sh` / `start-with-minio.sh`: documented convenience entry points. Moving them would require updating `docs/setup/minio.md` and `docs/architecture/minio-storage.md`. They can be revisited if the team prefers a `scripts/runners/` location with root-level symlinks.
- `streamlit_app_progressive.py`: primary Streamlit application file; well above the 200/300 LoC threshold anyway.

## Follow-up candidates

The `scripts/` root folder itself contains 56 code files, of which **40 are < 200 LoC** and **48 are < 300 LoC**. Several already live in appropriate subfolders (`scripts/analysis`, `scripts/maintenance`, etc.), but a future pass could look at:

- Very small runners in `scripts/runners/` that might merge or move.
- Deployment shell helpers in `scripts/deployment/` that may duplicate documented Makefile commands.
- Empty placeholder files (e.g., `scripts/maintenance/visualize_7x2_structure.py` at 0 LoC).
