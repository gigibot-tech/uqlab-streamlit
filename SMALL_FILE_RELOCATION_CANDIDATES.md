# Small File Relocation Candidates — Root Directory

## Scope

Checked the **repository root folder** (`/workspace`) for files smaller than **300 lines of code** (with a stricter 200-line threshold noted) and assessed whether they can be relocated to a more appropriate top-level directory.

## Methodology

- Line counts are from `wc -l` and include comments/blank lines.
- Reference checks were done with `grep` across `README.md`, `Makefile`, `docs/`, and `scripts/`.
- A move is marked **safe** when no in-repo references exist; otherwise it requires updating call sites.

## Current Root Files Under 300 LoC

| File | LoC | Category | Proposed Destination | References | Status |
|------|-----|----------|----------------------|------------|--------|
| `package-lock.json` | 6 | artifact | `scripts/` or delete if unused | none found | candidate |
| `streamlit_requirements.txt` | 10 | config/deployment | `scripts/deployment/` or merge into `pyproject.toml` | `scripts/deployment/run_streamlit.sh`, `scripts/deployment/run_streamlit_modular.sh`, docs | needs update |
| `docker-compose.yml` | 44 | infrastructure | `backend/` | `README.md` | needs update |
| `pytest.ini` | 46 | config | **keep at root** | test runner convention | keep |
| `mypy.ini` | 80 | config | **keep at root** | type-checker convention | keep |
| `start.sh` | 61 | deployment | `scripts/deployment/` | none found | safe candidate |
| `start-with-minio.sh` | 88 | deployment | `scripts/deployment/` or `backend/` | `docs/setup/minio.md`, `docs/architecture/minio-storage.md` | needs update |
| `pyproject.toml` | 116 | config | **keep at root** | package metadata convention | keep |
| `START_HERE.md` | 97 | documentation | `docs/` | none found | safe candidate |
| `analysis_results.txt` | 132 | generated output | `data/` or `docs/` | none found | safe candidate |
| `ARCHITECTURE_CLARIFICATION.md` | 171 | documentation | `docs/architecture/` | none found | safe candidate |

## Files Moved in This Change

The following maintenance-only files had no in-repo references and were relocated to `scripts/maintenance/`:

- `organize_root_scripts.sh` → `scripts/maintenance/organize_root_scripts.sh`
- `analyze_md_files.py` → `scripts/maintenance/analyze_md_files.py`

Both are clearly maintenance scripts; the first was already a stale relocation artifact that had done its original job, and the second is a diagnostic/markdown-analysis utility.

## Files to Keep at Root

These are small but should stay at the root by convention or because they are frequently referenced by external tooling:

- `pyproject.toml`
- `pytest.ini`
- `mypy.ini`
- `Makefile` (119 LoC, right above threshold, but conventionally root)
- `.gitignore`, `.env.example`, `.env.production.example`

## Risky Candidates Requiring Reference Updates

Moving these would require updating existing documentation or scripts:

- `docker-compose.yml` → `backend/`: update `README.md` line 30 and 246.
- `start-with-minio.sh` → `scripts/deployment/` or `backend/`: update `docs/setup/minio.md` and `docs/architecture/minio-storage.md`.
- `streamlit_requirements.txt` → `scripts/deployment/` or `src/streamlit_ui/`: update `scripts/deployment/run_streamlit*.sh` and several docs.

## Recommendation

1. Apply the safe moves already done (`organize_root_scripts.sh`, `analyze_md_files.py`).
2. Relocate `start.sh`, `START_HERE.md`, `analysis_results.txt`, and the architecture markdowns (`ARCHITECTURE_CLARIFICATION.md`) next; they are small, unreferenced, and better grouped with their respective functional areas.
3. Tackle `docker-compose.yml`, `start-with-minio.sh`, and `streamlit_requirements.txt` only after updating references to avoid breaking onboarding docs.
4. Delete or move `package-lock.json` if it is not needed; it is only 6 lines and may be an accidental artifact.
