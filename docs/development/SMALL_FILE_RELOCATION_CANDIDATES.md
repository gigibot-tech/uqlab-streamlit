# Small File Relocation Candidates – `workspace`

**Mode:** top-level only

**Folder:** `/workspace`

**Thresholds:** 200 / 300 non-blank lines

**Scanned files:** 32

**Candidates:** 23 under 200 lines, 4 between 200 and 300 lines


## Strong candidates (< 200 lines)

| File | Total | Non-blank | Suggested target | Rationale |
|------|-------|-----------|------------------|-----------|
| `.python-version` | 1 | 1 | `root` | Dotfile / tooling config (keep in root) |
| `.gitmodules` | 3 | 3 | `root` | Dotfile / tooling config (keep in root) |
| `package-lock.json` | 6 | 6 | `TBD` | No strong relocation heuristic; review manually |
| `streamlit_requirements.txt` | 10 | 9 | `root` | Requirements / ignore file (keep in root) |
| `.bobignore` | 15 | 12 | `root` | Dotfile / tooling config (keep in root) |
| `.ruffignore` | 18 | 18 | `root` | Dotfile / tooling config (keep in root) |
| `.env.example` | 30 | 24 | `root` | Dotfile / tooling config (keep in root) |
| `pytest.ini` | 46 | 38 | `root` | Tooling configuration (keep in root) |
| `docker-compose.yml` | 44 | 40 | `configs/` | YAML configuration |
| `start.sh` | 61 | 47 | `scripts/deployment/` | Shell start-up / deployment script |
| `organize_root_scripts.sh` | 57 | 48 | `scripts/deployment/` | Shell start-up / deployment script |
| `.env.production.example` | 69 | 52 | `root` | Dotfile / tooling config (keep in root) |
| `analyze_md_files.py` | 63 | 53 | `scripts/maintenance/` | Python utility/migration script |
| `mypy.ini` | 80 | 59 | `root` | Tooling configuration (keep in root) |
| `start-with-minio.sh` | 88 | 69 | `scripts/deployment/` | Shell start-up / deployment script |
| `START_HERE.md` | 97 | 70 | `docs/development/` | Documentation / analysis report |
| `Makefile` | 119 | 102 | `root` | Build / deployment orchestration (keep in root) |
| `pyproject.toml` | 116 | 102 | `root` | Python project metadata (keep in root) |
| `analysis_results.txt` | 132 | 111 | `root` | Requirements / ignore file (keep in root) |
| `ARCHITECTURE_CLARIFICATION.md` | 171 | 117 | `docs/development/` | Documentation / analysis report |
| `.gitignore` | 150 | 128 | `root` | Dotfile / tooling config (keep in root) |
| `EXECUTION_FLOW_AND_CONFIG_GUIDE.md` | 229 | 170 | `docs/development/` | Documentation / analysis report |
| `DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md` | 235 | 177 | `docs/development/` | Documentation / analysis report |

## Medium candidates (200–299 lines)

| File | Total | Non-blank | Suggested target | Rationale |
|------|-------|-----------|------------------|-----------|
| `TERMINOLOGY_CLARIFICATION.md` | 275 | 204 | `docs/development/` | Documentation / analysis report |
| `FINAL_ARCHITECTURE_DECISION.md` | 300 | 229 | `docs/development/` | Documentation / analysis report |
| `PACKAGE_REORGANIZATION_PROPOSAL.md` | 296 | 234 | `docs/development/` | Documentation / analysis report |
| `README.md` | 366 | 267 | `docs/development/` | Documentation / analysis report |

## Files at or above 300 lines (likely stay)

| File | Total | Non-blank | Notes |
|------|-------|-----------|-------|
| `ARCHITECTURE_IMPROVEMENT_PROPOSAL.md` | 417 | 323 | Documentation / analysis report |
| `streamlit_app_progressive.py` | 370 | 328 | Python utility/migration script |
| `IMPORT_GUIDE.md` | 492 | 358 | Documentation / analysis report |
| `COMPLETE_SYSTEM_FLOW.md` | 499 | 408 | Documentation / analysis report |
| `dependencies.json` | 21420 | 21420 | No strong relocation heuristic; review manually |

## Notes

- Suggestions are based on filename/extension heuristics and this repo's conventions.

- Before moving any file, verify it is not referenced by absolute path from CI/CD, Docker, or documentation.

- Dotfiles (`.env.example`, `.gitignore`, `.python-version`, etc.) and project metadata (`pyproject.toml`) are intentionally kept in the root.
