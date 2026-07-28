# Small File Relocation Candidates — `scripts/` Root Audit

This audit checks the `scripts/` root folder for code files under **200/300 LoC** and identifies whether they can be relocated to a more appropriate subdirectory.

## Analyzed folder

`scripts/` (immediate files only, not recursively entering subfolders)

## Thresholds

- **< 200 LoC**: strong relocation candidate when the file is a standalone utility.
- **< 300 LoC**: still small, but kept at the folder root if it is a documented entry-point or conventionally located there.

## `scripts/` root code files found

| File | LoC | Threshold | Entry-point / documented | Relocation action |
|------|-----|-----------|--------------------------|-------------------|
| `regenerate_shims.py` | 34 | < 200 | No | **Moved to `scripts/maintenance/regenerate_shims.py`** |
| `migrate_to_uqlab_core.py` | 111 | < 200 | No | **Moved to `scripts/maintenance/migrate_to_uqlab_core.py`** |
| `README.md` | 446 | > 300 | Yes (folder documentation) | **Kept at `scripts/` root** |
| `validate_per_class_campaign.py` | 493 | > 300 | Yes (documented campaign runner) | **Kept at `scripts/` root** |

## Files moved

### `regenerate_shims.py` → `scripts/maintenance/`

- Purpose: regenerate compatibility shims between the legacy `uqlab` package and the new `uqlab_core` package.
- Change: updated `Path(__file__).resolve().parents[1]` to `parents[2]` so the repo root is still resolved correctly from the new location.
- No other references found in the repo.

### `migrate_to_uqlab_core.py` → `scripts/maintenance/`

- Purpose: one-shot migration that copies core modules from `uqlab` to `uqlab_core` and leaves compatibility shims behind.
- Change: updated `Path(__file__).resolve().parents[1]` to `parents[2]` so the repo root is still resolved correctly from the new location.
- No other references found in the repo.

## Files kept at `scripts/` root and why

- `README.md`: folder-level documentation; conventionally lives at the root of the folder it describes.
- `validate_per_class_campaign.py`: above the 300 LoC threshold and appears to be a documented standalone runner.

## Follow-up candidates

Other `scripts/` subfolders also contain small files, but they are already grouped logically. A future pass could consider:

- `scripts/maintenance/visualize_7x2_structure.py` (0 LoC): empty placeholder; either implement or remove.
- `scripts/runners/run_fast.py` (12 LoC): very thin runner; could be merged with a related runner or documented as a minimal CLI example.
- `scripts/deployment/run_streamlit.sh` and `run_streamlit_modular.sh` (31 / 11 LoC): small deployment wrappers that may duplicate documented `Makefile` / `start.sh` commands.
