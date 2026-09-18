# Small Root Folder Relocation Candidates – `workspace`

**Root analyzed:** `/workspace`

**Thresholds:** files under 200 LoC are strong candidates, files under 300 LoC are medium candidates

**Found:** 1 root folder(s) whose files all fall below the thresholds


## Strong candidates (all files < 200 lines)

| Folder | Files | Max | Median | Suggested target | Rationale |
|--------|-------|-----|--------|------------------|-----------|
| `configs` | 11 | 58 | 32 | `src/uqlab_core/configs/` | Package configs with the ML core library |

## Medium candidates (all files < 300 lines)

_No medium candidates found._


## References per candidate


### `configs`

Referenced by:
- `ARCHITECTURE_CLARIFICATION.md`
- `COMPLETE_SYSTEM_FLOW.md`
- `EXECUTION_FLOW_AND_CONFIG_GUIDE.md`
- `FINAL_ARCHITECTURE_DECISION.md`
- `README.md`
- `START_HERE.md`
- `configs/README.md`
- `docs/LAUNCH_TO_VISUALIZATION_FLOW.md`
- `docs/architecture-design/FINAL_ARCHITECTURE_SCHEMA_UNIFIED.md`
- `docs/architecture-design/FINAL_ARCHITECTURE_SUMMARY.md`


## Notes

- By default all files inside each root subfolder are considered (equivalent to `--recursive`). Pass `--no-recursive` to look only at direct files.

- Folders such as `src/`, `tests/`, `data/`, and tooling metadata (`.git`, `.cursor`, `.vscode`) are intentionally skipped.

- Before moving any folder, verify consumers such as Dockerfiles, CI/CD, READMEs, import paths, and `runtime_paths.configs_dir()`.

- Suggestions are based on folder name and content heuristics; review manually before relocating.
