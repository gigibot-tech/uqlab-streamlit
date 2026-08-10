# Small file relocation candidates for `/workspace`

Threshold: **≤300 LoC** (physical lines).

| File | LoC | Binary | Suggested destination | Reason |
|------|-----|--------|----------------------|--------|
| `.DS_Store` | N/A | yes | `REMOVE` | macOS metadata file |
| `.bobignore` | 15 | no | `KEEP` | Bob ignore configuration |
| `.env.example` | 30 | no | `KEEP` | example environment files |
| `.env.production.example` | 69 | no | `KEEP` | example environment files |
| `.gitignore` | 150 | no | `KEEP` | git configuration |
| `.gitignore_parent` | 119 | no | `KEEP` | git configuration |
| `.gitmodules` | 3 | no | `KEEP` | git configuration |
| `.python-version` | 1 | no | `KEEP` | Python version pin |
| `.ruffignore` | 18 | no | `KEEP` | Ruff ignore configuration |
| `2408.12175v3.pdf` | N/A | yes | `docs/assets/` | reference documents / papers |
| `ARCHITECTURE_CLARIFICATION.md` | 171 | no | `docs/architecture/` | architecture / decision documentation |
| `DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md` | 235 | no | `docs/development/` | proposal / analysis documentation |
| `EXECUTION_FLOW_AND_CONFIG_GUIDE.md` | 229 | no | `docs/user-guides/` | user / developer guide |
| `FINAL_ARCHITECTURE_DECISION.md` | 300 | no | `docs/archive/` | appears to be historical/archived documentation |
| `Makefile` | 119 | no | `KEEP` | build tooling |
| `PACKAGE_REORGANIZATION_PROPOSAL.md` | 296 | no | `docs/development/` | proposal / analysis documentation |
| `START_HERE.md` | 97 | no | `KEEP` | root README / onboarding doc |
| `TERMINOLOGY_CLARIFICATION.md` | 275 | no | `docs/archive/` | appears to be historical/archived documentation |
| `analysis_results.txt` | 132 | no | `data/` | generated or auxiliary text data |
| `analyze_md_files.py` | 63 | no | `scripts/maintenance/` | utility/maintenance Python scripts |
| `docker-compose.yml` | 44 | no | `KEEP` | Docker compose configuration |
| `mypy.ini` | 80 | no | `KEEP` | tooling configuration |
| `organize_root_scripts.sh` | 57 | no | `scripts/maintenance/` | utility/maintenance shell scripts |
| `package-lock.json` | 6 | no | `REMOVE` | ignored lock file; safe to delete if not needed |
| `pyproject.toml` | 116 | no | `KEEP` | project/tooling configuration |
| `pytest.ini` | 46 | no | `KEEP` | tooling configuration |
| `start-with-minio.sh` | 88 | no | `KEEP` | top-level entry/start script |
| `start.sh` | 61 | no | `KEEP` | top-level entry/start script |
| `streamlit_requirements.txt` | 10 | no | `KEEP` | Streamlit requirements referenced by start scripts |
| `three_axioms_demonstration.png` | N/A | yes | `docs/assets/` | image assets |

*Note: suggestions are heuristic. Verify references before moving any file.*