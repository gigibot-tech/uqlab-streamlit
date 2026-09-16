# Root Small Files Reorganization

**Date**: 2026-09-16  
**Trigger**: Cron automation — review root-level files under 200/300 LoC and relocate where safe.

---

## Summary

Scanned `/workspace` (project root). Found **23 root files ≤ 300 lines** (excluding binary/lock artifacts). Three non-document files were safely relocated; the remaining items are configuration, entry points, or linked Markdown docs with clear target folders documented below.

The `docs/features/` folder was reviewed before deciding destinations; the small root documents are architecture/development artifacts rather than feature specs, so they map to `docs/architecture/`, `docs/development/`, or `docs/archive/` instead.

---

## Files Moved This Run

| File | Original LoC | Moved To | Reason |
|------|--------------|----------|--------|
| `analyze_md_files.py` | 63 | `scripts/maintenance/analyze_md_files.py` | One-off utility for categorizing Markdown files; fits maintenance scripts. |
| `organize_root_scripts.sh` | 57 | `scripts/maintenance/organize_root_scripts.sh` | Shell helper that organizes root scripts; self-described maintenance script. |
| `analysis_results.txt` | 132 | `data/analysis_results.txt` | Generated experiment output, not source code. |

**Reference updated**: `docs/validation/HYPOTHESIS_VERIFICATION_RESULTS.md` now links to `data/analysis_results.txt`.

---

## Root Files That Should Stay (by convention)

These are small but conventionally belong at the project root.

| File | LoC | Why It Stays |
|------|-----|--------------|
| `.python-version` | 1 | pyenv version pin |
| `.gitmodules` | 3 | Git submodule config |
| `package-lock.json` | 6 | npm lockfile (root-level) |
| `streamlit_requirements.txt` | 10 | Entry-point requirements referenced by startup docs |
| `.DS_Store` | 13 | macOS metadata (should be gitignored, not moved) |
| `.bobignore` | 14 | Bob assistant ignore rules |
| `.ruffignore` | 17 | Ruff ignore rules |
| `.env.example` | 29 | Environment template |
| `docker-compose.yml` | 44 | Docker orchestration |
| `pytest.ini` | 46 | pytest config |
| `mypy.ini` | 80 | mypy config |
| `.env.production.example` | 68 | Production env template |
| `pyproject.toml` | 116 | Python project metadata |
| `.gitignore_parent` | 118 | Parent gitignore |
| `Makefile` | 119 | Build/run commands |
| `.gitignore` | 150 | Git ignore rules |
| `START_HERE.md` | 97 | Deliberate root onboarding stub |

---

## Small Docs Recommended for Relocation

These Markdown files are **≤ 300 LoC** and have a logical home under `docs/`. Moving them requires updating the relative links in `README.md` and the cross-references shown below.

### Candidates under 200 LoC

| File | LoC | Recommended Destination | Notes / Blockers |
|------|-----|------------------------|------------------|
| `ARCHITECTURE_CLARIFICATION.md` | 171 | `docs/architecture/ARCHITECTURE_CLARIFICATION.md` | Linked from `README.md` and `COMPLETE_SYSTEM_FLOW.md`. Update links if moved. |

### Candidates between 200–300 LoC

| File | LoC | Recommended Destination | Notes / Blockers |
|------|-----|------------------------|------------------|
| `EXECUTION_FLOW_AND_CONFIG_GUIDE.md` | 229 | `docs/development/EXECUTION_FLOW_AND_CONFIG_GUIDE.md` | Linked from `README.md`. |
| `DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md` | 234 | `docs/development/DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md` | Links to `PACKAGE_REORGANIZATION_PROPOSAL.md`; update if both move. |
| `TERMINOLOGY_CLARIFICATION.md` | 274 | `docs/architecture/TERMINOLOGY_CLARIFICATION.md` | Links to `FINAL_ARCHITECTURE_DECISION.md`. |
| `PACKAGE_REORGANIZATION_PROPOSAL.md` | 295 | `docs/development/PACKAGE_REORGANIZATION_PROPOSAL.md` | Referenced by `DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md`. |
| `FINAL_ARCHITECTURE_DECISION.md` | 299 | `docs/archive/FINAL_ARCHITECTURE_DECISION.md` | Header already says **"Superseded"**; best as an archived redirect. |

### Larger docs that still merit relocation

| File | LoC | Recommended Destination | Notes |
|------|-----|------------------------|-------|
| `IMPORT_GUIDE.md` | 491 | `docs/development/IMPORT_GUIDE.md` | Developer reference; >300 LoC but still a relocation candidate. |

---

## Entry Points and Apps to Keep at Root

| File | LoC | Reason |
|------|-----|----------|
| `README.md` | 366 | Main project landing page |
| `streamlit_app_progressive.py` | 370 | Primary Streamlit entry point invoked by `Makefile` and docs |
| `start.sh` | 61 | Referenced in `streamlit_requirements.txt`; convenient startup wrapper |
| `start-with-minio.sh` | 88 | Referenced in `docs/architecture/minio-storage.md` and `docs/setup/minio.md` |

---

## Recommended Next Steps

1. **Move the six Markdown relocation candidates** listed above to their target folders, then update the following links:
   - `README.md` lines 49–50 → `docs/development/EXECUTION_FLOW_AND_CONFIG_GUIDE.md` and `docs/architecture/ARCHITECTURE_CLARIFICATION.md`
   - `TERMINOLOGY_CLARIFICATION.md` line 269 → `docs/archive/FINAL_ARCHITECTURE_DECISION.md`
   - `DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md` line 215 → `docs/development/PACKAGE_REORGANIZATION_PROPOSAL.md`
   - `COMPLETE_SYSTEM_FLOW.md` line 6 → `docs/architecture/ARCHITECTURE_CLARIFICATION.md`

2. **Consider replacing** superseded root docs with one-line redirect stubs (the pattern already used in `docs/archive/SYSTEM_FLOW.md` and `docs/archive/REGISTRIES.md`) so old bookmarks still work.

3. **Review `start.sh` and `start-with-minio.sh`** for possible relocation to `scripts/shell/` after updating `Makefile`, `streamlit_requirements.txt`, and MinIO docs.

4. **Add `.DS_Store` to `.gitignore`** if it is not already ignored.

---

## Reuse Check: `docs/features/`

The `docs/features/` directory contains functional feature documentation (workflow-config, signal-registry, evaluation-protocol, etc.). The small root files reviewed here are historical architecture/development notes and proposals, so they do **not** belong in `docs/features/`. No feature docs needed to be modified or duplicated for this reorganization.
