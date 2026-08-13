# Small-file relocation

Root-level folders whose files are all small (< 200–300 LoC) are good candidates for
relocation into a package or a more appropriate location.

## Tool

[`scripts/maintenance/detect_small_file_relocation_candidates.py`](../../scripts/maintenance/detect_small_file_relocation_candidates.py)

```bash
python3 scripts/maintenance/detect_small_file_relocation_candidates.py
```

A folder qualifies when every text file inside it is below the largest threshold
(default 300 LoC). This deliberately excludes large roots such as `backend/`,
`docs/`, `scripts/`, `src/`, and `tests/` that contain many tiny files but are not
practical to move as a unit.

## Current status

- ✅ `configs/` was the only qualifying root folder (all 11 YAML files ≤ 64 LoC).
  It has been relocated to `src/uqlab_core/configs/` and all consumers updated.
- No other root folders currently meet the candidate criteria.

## Related

- `docs/ROOT_SMALL_FILE_RELOCATION_CANDIDATES.md` — candidate inventory (added in
  parallel work).
- `PACKAGE_REORGANIZATION_PROPOSAL.md` — broader package separation discussion.
