# Small File Relocation Candidates — `docs/features/`

> **Scope:** Check the `docs/features/` folder (the project’s feature-documentation index) for files under 200/300 LoC and determine whether they can be relocated to a more appropriate home.

## Summary

- **Folder:** `/workspace/docs/features/`
- **Files:** 18 markdown files
- **< 200 LoC:** 15 files (83%)
- **200–300 LoC:** 1 file (`evaluation-protocol.md`, 279 LoC)
- **> 300 LoC:** 1 file (`sweep-grouping.md`, 340 LoC)
- **Verdict:** Most files are small enough to relocate or consolidate. The main cost is updating cross-references from `src/`, `START_HERE.md`, and the `.cursor/skills/` skill registry.

## File Inventory

| File | LoC | Topic | Fit in `docs/features/` | Proposed location | Notes |
|---|---|---|---|---|---|
| `README.md` | 23 | Index | Good | **Keep** | Required index for the folder |
| `ATTRIBUTION_ARTIFACTS.md` | 43 | Attribution artifacts | OK | `docs/signals/` or merge into `signal-registry.md` | Already linked from `evaluation-protocol.md` |
| `registries.md` | 44 | Registry overview | OK | `docs/signals/` or merge into `signal-registry.md` | Very small; duplication risk with `signal-registry.md` |
| `ui-debug.md` | 53 | Streamlit UI debug | **Poor** | `docs/streamlit/` | Strong candidate — moved in this branch |
| `four-region-partition.md` | 62 | Four-region data split | OK | `docs/validation/` or `docs/architecture/` | Tied to validation methodology |
| `validation-sweeps.md` | 62 | Validation sweep grids | OK | `docs/validation/` | Already validation-focused |
| `run-recovery.md` | 66 | Recover failed runs | OK | `docs/troubleshooting/` | Operational/recovery topic |
| `evaluation-pipeline.md` | 69 | Evaluation pipeline | OK | `docs/validation/` | Evaluation methodology |
| `four-region-notebook.md` | 69 | Four-region notebook guide | **Poor** | `docs/validation/` | Documents a notebook workflow, not a standalone feature |
| `checkpoint-arsenal.md` | 74 | Checkpoint review | OK | `docs/troubleshooting/` or `docs/validation/` | Recovery/debugging topic |
| `PAPER_FLOW.md` | 75 | Paper API → UQLab mapping | OK | `docs/user-guides/` or `docs/architecture/` | User-facing API map |
| `dataset-plugin.md` | 77 | Dataset plugin contract | OK | `docs/validation/` or `docs/architecture/` | Data layer extension guide |
| `data-pipeline.md` | 90 | Data pipeline walkthrough | OK | `docs/validation/` or `docs/architecture/` | Canonical data walkthrough |
| `disentanglement-benchmark.md` | 101 | Paper metric + plots | OK | `docs/validation/` | Benchmarking methodology |
| `signal-registry.md` | 121 | EK-FAK signal registry | OK | `docs/signals/` | Signal-specific documentation |
| `workflow-config.md` | 167 | Wizard → YAML mapping | OK | `docs/streamlit/` or `docs/user-guides/` | UI wizard configuration |
| `evaluation-protocol.md` | 279 | End-to-end protocol | Borderline | `docs/validation/` | Larger, but still fits validation methodology |
| `sweep-grouping.md` | 340 | Campaign grouping | OK | `docs/validation/` | Already referenced from `docs/README.md` |

## Immediate Moves (Implemented in This Branch)

### `ui-debug.md` → `docs/streamlit/ui-debug.md`

- **Rationale:** Content is exclusively about Streamlit UI debug surfaces; `docs/streamlit/` already hosts Streamlit-specific docs.
- **References updated:**
  - `docs/features/README.md`
  - `.cursor/skills/ui-debug/SKILL.md`
  - `START_HERE.md`

### `four-region-notebook.md` → `docs/validation/four-region-notebook.md` (Recommended)

- **Rationale:** The file documents the `notebooks/four_region_benchmark.ipynb` workflow, not a standalone UI feature. `docs/validation/` is the natural home for methodology docs.
- **References to update if implemented:**
  - `docs/features/README.md`
  - `docs/features/PAPER_FLOW.md`
  - `docs/features/four-region-partition.md`
  - `docs/features/evaluation-pipeline.md`
  - `src/uqlab_core/data/README.md`
  - `src/uqlab_core/evaluation/README.md`

## Alternative: Reorganize Within `docs/features/`

If the `features/` namespace should be preserved, group the remaining small files into subfolders by topic:

- `docs/features/data/` — `data-pipeline.md`, `four-region-partition.md`, `dataset-plugin.md`, `four-region-notebook.md`
- `docs/features/evaluation/` — `evaluation-pipeline.md`, `evaluation-protocol.md`, `disentanglement-benchmark.md`
- `docs/features/signals/` — `signal-registry.md`, `registries.md`, `ATTRIBUTION_ARTIFACTS.md`
- `docs/features/sweeps/` — `validation-sweeps.md`, `sweep-grouping.md`, `run-recovery.md`, `checkpoint-arsenal.md`
- `docs/features/ui/` — `workflow-config.md`, `ui-debug.md`
- `docs/features/paper/` — `PAPER_FLOW.md`

This keeps the feature docs together while removing the flat, hard-to-scan directory.

## Reference Impact Map

Moving any file from `docs/features/` requires updating these known references:

- `docs/features/README.md` — index table
- `docs/README.md` — Features section and quick navigation
- `START_HERE.md` — wizard and UI debug links
- `.cursor/skills/ui-debug/SKILL.md` — human-facing mirror doc link
- `docs/signals/UNCERTAINTY_SUBSET_LOGIC.md` — `evaluation-protocol.md` link
- `src/uqlab_core/runner/experiment_core.py` — `PAPER_FLOW.md` docstring
- `src/uqlab_core/run_artifacts.py` — `PAPER_FLOW.md` docstring
- `src/uqlab_core/models/README.md` — `disentanglement-benchmark.md` link
- `src/uqlab_core/evaluation/README.md` — multiple `docs/features/*` links
- `src/uqlab_core/evaluation/signals/README.md` — `signal-registry.md` link
- `src/uqlab_core/data/README.md` — multiple `docs/features/*` links
- `docs/archive/SIGNAL_NAMES_CENTRALIZATION.md` — `signal-registry.md` link
- `docs/archive/REGISTRIES.md` — `registries.md` link
- `docs/archive/CHECKPOINT_ARSENAL_IMPLEMENTATION_PLAN.md` — `checkpoint-arsenal.md` link
- `docs/architecture/evaluation-pipeline.md` — `evaluation-protocol.md` link

## Recommendation

1. **Move `ui-debug.md`** to `docs/streamlit/` — clear win, low risk. (Done.)
2. **Consider moving `four-region-notebook.md`** to `docs/validation/` — it documents a notebook, not a feature.
3. **For the remaining small files**, choose one of:
   - **Option A (preferred):** Move them to topic-specific `docs/` folders (`validation/`, `signals/`, `troubleshooting/`, `streamlit/`, `user-guides/`). This aligns with the documented category structure in `docs/README.md`.
   - **Option B:** Keep them under `docs/features/` but reorganize into subfolders by topic. This preserves the existing `features/` namespace and reduces flat clutter.
4. **Avoid moving the index** (`README.md`) unless the folder itself is removed.
5. **Update all cross-references** after each move; the reference map above is the known surface area.
