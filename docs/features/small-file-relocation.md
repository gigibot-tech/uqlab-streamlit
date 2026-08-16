# Small-file root-folder relocation

This doc tracks the periodic cleanup that moves small root-level folders/files into the public `docs/` tree or the appropriate package directory.

## `.docs/` → `docs/deployment/` + `docs/development/` (this run)

The hidden root folder `.docs/` contained only small markdown guides (all under 300 LoC) and deployment screenshots.

| Source | Destination | Notes |
|--------|-------------|-------|
| `.docs/ce-deployment.md` | `docs/deployment/ce-deployment.md` | IBM Code Engine guide |
| `.docs/oc-deployment.md` | `docs/deployment/oc-deployment.md` | OpenShift guide; internal link to `scripts/README.md` adjusted for new depth |
| `.docs/development.md` | `docs/development/development.md` | Docker Compose / local dev |
| `.docs/maintenance.md` | `docs/development/maintenance.md` | Template maintenance workflow |
| `.docs/release-notes.md` | `docs/development/release-notes.md` | Version history |
| `.docs/img/*.png` | `docs/deployment/img/*.png` | Screenshots (no markdown references found) |

### Reference updates

- `.env.production.example` — comments now point to `docs/deployment/oc-deployment.md`
- `scripts/README.md` — deployment guide links updated to `docs/deployment/oc-deployment.md`
- `backend/README.md` — development guide link updated to `docs/development/development.md`
- `docs/README.md` — populated `Deployment` and `Development` index sections and quick navigation

### Broken symlink cleanup

The following stale symlinks were also removed because their targets no longer exist:

- `uq_benchmarks` → `src/uqlab/4_evaluation/benchmarks`
- `uq_classification` → `src/uqlab/classification`
- `notebooks/validation/notebook_support` → `../../../src/walaris/notebook_support`

## Verification checklist

- `rg '\.docs/'` returns no matches.
- All markdown links resolve from their new directory depth.
- `docs/README.md` lists the relocated docs.

## Remaining candidates

- `analyze_md_files.py` at repo root (63 LoC) — could move to `scripts/diagnostics/` or `scripts/maintenance/`.
- `docs/features/` files (mostly under 300 LoC) — can be grouped into subfolders by topic or moved to sibling categories (`docs/validation/`, `docs/signals/`, `docs/troubleshooting/`, `docs/streamlit/`, `docs/user-guides/`).
