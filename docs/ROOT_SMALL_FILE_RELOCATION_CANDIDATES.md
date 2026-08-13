# Root Small-File Relocation Candidates

Inventory of root-level folders that qualify as "small-file relocation candidates"
(all files below 200–300 LoC) and the status of each.

## Tool

[`scripts/maintenance/detect_small_file_relocation_candidates.py`](../scripts/maintenance/detect_small_file_relocation_candidates.py)

```bash
python3 scripts/maintenance/detect_small_file_relocation_candidates.py
```

## Criteria

A root folder qualifies when every tracked text file inside it is below the
threshold (default 300 LoC). This intentionally excludes large package roots
(`backend/`, `docs/`, `scripts/`, `src/`, `tests/`) that contain many tiny files
but are not practical to move as a unit.

## Current status (after latest relocation)

| Folder | Status | Notes |
|--------|--------|-------|
| `configs/` | ✅ Relocated | Moved to `src/uqlab_core/configs/`. All consumers and docs updated. |
| `uqlab-flask/` | Not a candidate | Contains `executor.py` (652 LoC) and `wizard.py` (282 LoC), so it exceeds the threshold. |
| `data/` | Not a candidate | Only contains a `.gitkeep` marker. |

## No remaining candidates

After moving `configs/`, the scanner reports no remaining root folders where every
file is below the 300 LoC threshold.
