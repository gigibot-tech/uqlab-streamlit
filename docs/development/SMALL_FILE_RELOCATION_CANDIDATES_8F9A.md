# Small-File Relocation Candidates — 8f9a

This report documents a small-file relocation pass for the `docs/troubleshooting/`
folder. All Markdown files in the folder are under the 200/300 LoC threshold, and
the folder is only referenced from the documentation index, so it can be cleanly
archived.

## Analyzed folder

`docs/troubleshooting/` (a docs root-level subfolder)

## Thresholds

- **< 200 LoC**: strong relocation candidate for a standalone doc page.
- **< 300 LoC**: still small; kept only if it is a high-traffic current guide.

## Files in `docs/troubleshooting/`

| File | LoC | Threshold | Notes |
|------|-----|-----------|-------|
| `label-noise-sweep.md` | 109 | < 200 | Historical fix notes |
| `progressive-ui.md` | 174 | < 200 | UI fix notes |
| `resnet-feature-extractor.md` | 116 | < 200 | Model fix notes |
| `startup-issues.md` | 141 | < 200 | Startup fix notes |

**Summary:** 4 files, max 174 LoC, total 540 LoC. All files are below the 200 LoC threshold.

## Relocation action

Move `docs/troubleshooting/` to `docs/archive/troubleshooting/`.

Rationale:

- The pages are historical bug-fix notes rather than active user guides.
- The docs archive already exists for superseded documentation.
- Only `docs/README.md` links to these pages, so the change is low-risk.
- Keeping the folder under `docs/archive/` preserves the content while making it
clear that the guides are no longer maintained as primary docs.

## Updated consumers

- `docs/README.md`: troubleshooting section removed from the active index and
replaced with a note pointing to the archived location.
- No other code or documentation references `docs/troubleshooting/`.

## Follow-up candidates

- `docs/debug/` contains a single 72 LoC file (`EVAL_ARTIFACTS.md`) and is
referenced from `docs/architecture/evaluation-pipeline.md`. It could be archived in
a separate pass if the artifact guide is no longer current.
- `tests/legacy/` contains 11 test files all under 300 LoC (max 215). A future
pass could evaluate whether these legacy tests should move to `tests/archive/`
or be merged with the main test suite.
