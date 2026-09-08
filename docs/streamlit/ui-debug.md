# UI debug (progressive app)

Hide or show blocks in [`streamlit_app_progressive.py`](../../streamlit_app_progressive.py) without deleting code.

**Where:** sidebar footer → **UI debug — components**

**Agent workflow:** [`.cursor/skills/ui-debug/SKILL.md`](../../.cursor/skills/ui-debug/SKILL.md)

## Quick actions

| Button | Effect |
|--------|--------|
| **All on** | Every registered toggle on (auto-refresh still off until you enable it) |
| **Results off** | Hides entire Results area + footer metrics |
| **Results defaults** | Results on; §1 progress/auto-refresh and per-run details off |

## Results §1–§4 toggles

| Section | Primary toggle |
|---------|----------------|
| Entire block | `Results · entire section` |
| §1 Live status | `Results · §1 live status` |
| §2 3-line sweep plots | `Results · §2 sweep analysis` |
| §3 Campaign expanders | `Results · §3 campaign expanders` |
| §3 Per-run metrics (AUROC tables) | `Results · per-run details + bar charts` |
| §4 Training data | `Results · training data inspection` |

### Per-run details parent chain

`results_experiment_details` is **off by default** and requires two ancestors enabled:

1. `Results · entire section` (`results_section`)
2. `Results · §3 campaign expanders` (`results_sweep_campaigns`)
3. Then enable **↳ Results · per-run details + bar charts**

When per-run details is on, **5s auto-rerun (JS)** is automatically turned off — heavy per-run rendering and scheduled reruns do not combine.

Parent toggles cascade: turning off **entire section** disables all children.

## Launch toggles

| Toggle | What it gates |
|--------|----------------|
| `Step 5 · launch buttons` | Primary + Run all cards in Step 5 |
| `Step 5 / Results · plot probe redo suggestions` | Duplicate-gated plot probe panels |
| `Sidebar · quick launch` | Same cards in the sidebar |
| `Launch result banner` | Success/error banner after launch |

## If Results “disappears”

1. Open **UI debug** → enable **Results · entire section** (or **Results defaults**).
2. Scroll below Step 5 — Results is not in the sidebar.
3. §2 plots need ≥2 **completed** runs with `results.pt` on disk.
