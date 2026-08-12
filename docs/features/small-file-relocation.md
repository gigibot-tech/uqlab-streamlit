# Small-file relocation candidates

Identify root-level folders whose files are small enough that the whole folder could
be relocated into a package or merged into a more appropriate location.

## Tool

[`scripts/maintenance/find_small_file_relocation_candidates.py`](../../scripts/maintenance/find_small_file_relocation_candidates.py)

Usage:

```bash
python3 scripts/maintenance/find_small_file_relocation_candidates.py \
  --root /workspace --thresholds 200 300
```

Optional JSON output:

```bash
python3 scripts/maintenance/find_small_file_relocation_candidates.py \
  --root /workspace --thresholds 200 300 --output /tmp/candidates.json
```

The script uses these heuristics to flag a folder as a candidate:

- total files <= 50
- median lines <= largest threshold (default 300)
- average lines <= largest threshold (default 300)
- >= 75% of files under the largest threshold

This intentionally excludes large roots such as `backend/`, `docs/`, `scripts/`,
`src/`, and `tests/` that contain many tiny files but are not practical to move as
a unit.

## Current findings (200 / 300 LoC thresholds)

Two root folders meet the candidate criteria:

| Folder | Files | Median lines | Average lines | Files <= 300 LoC | Notes |
|--------|-------|--------------|---------------|------------------|-------|
| `uqlab-flask/` | 17 | 25 | 104.0 | 16 (94.1%) | Self-contained Flask UI; one outlier at 652 LoC (`executor.py`) |
| `configs/` | 11 | 40 | 38.9 | 11 (100%) | YAML examples and experiment defaults |

### `uqlab-flask/`

This is the strongest candidate. It is a lean Flask UI that sits at the project root
but is conceptually a frontend package, separate from the ML core (`src/uqlab/`),
the orchestrator (`src/uqlab_orchestrator/`), and the FastAPI backend (`backend/`).

[PACKAGE_REORGANIZATION_PROPOSAL.md](../../PACKAGE_REORGANIZATION_PROPOSAL.md) already
recommends moving the Streamlit UI out of `src/uqlab/` into a dedicated UI package.
`uqlab-flask` fits the same pattern.

Suggested destinations:

- `src/uqlab_flask/` — make it a workspace package alongside `src/uqlab` and
  `src/uqlab_core`.
- `src/flask_ui/` — if the project wants a neutral `*_ui` naming convention for all
  frontends (Streamlit would become `src/streamlit_ui/` per the existing proposal).

Files to watch during a move:

- `uqlab-flask/app.py` — hard-codes `PROJECT_ROOT` and `EXPERIMENTS_DIR` paths.
- `uqlab-flask/uqlab_flask/executor.py` — largest file (652 LoC); consider splitting
  the worker logic from the sweep/job bookkeeping before or during the move.
- `docs/UQLAB_FLOW.md` and `START_HERE.md` — external references to `uqlab-flask`.

### `configs/`

All 11 files are under 100 LoC. It is a valid candidate by the numbers, but YAML
configuration at the project root is a common and acceptable pattern. Before moving
it, confirm whether any launcher or backend code expects configs at the root path.

If relocation is still desired, sensible destinations:

- `src/uqlab/configs/` — if the configs are tied to the ML package.
- `backend/app/configs/` — if they are primarily backend runtime defaults.

## Non-candidates

The remaining root folders are either too large to move as a unit or have a mix of
small and large files:

- `backend/` — 102 files, median 51 lines; large FastAPI service, not a relocation target.
- `docs/` — 346 files, median 88 lines; documentation root should stay at top level.
- `notebooks/` — 21 files, median 305 lines; several notebooks exceed 300 LoC.
- `scripts/` — 59 files, median 124 lines; already the intended home for scripts.
- `src/` — 67 files, median 129 lines; this is the core package root.
- `tests/` — 63 files, median 86 lines; test suite should stay at top level.
- `data/` — only contains a `.gitkeep` marker; not a meaningful relocation target.

## Next steps

1. Decide whether to relocate `uqlab-flask/` (recommended) and pick a destination.
2. If moving, update workspace/package metadata, import paths, and documentation.
3. Leave `configs/` at root unless a stronger architectural reason emerges.
4. Re-run the tool after any move to verify the candidate list shrinks.
