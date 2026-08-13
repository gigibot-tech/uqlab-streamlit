# Failed experiment recovery (finalize from disk)

Recover **failed** runs that already finished training and signal collection on disk but died before `summary.json` / `results.pt` were written. Recovery **does not re-train** models.

## Recovery tiers

| Tier | Disk condition | Action |
|------|----------------|--------|
| `db_sync` | `summary.json` or `results.pt` exists; DB still `failed` or missing AUROC | Load artifacts → `experiment_repository.save_results()` |
| `zwischen_finalize` | `zwischen/00_eval_setup.pt` + `05_signal_table.pt`; no summary | Re-run scoring + persist (no training) |
| `partial` | Some `zwischen/` stages but missing `00` or `05` | Report missing stages; no auto-fix |
| `none` | No usable artifacts | Not recoverable |

Implementation: `src/uqlab/evaluation/pipeline/run_recovery.py`.

## Required `zwischen` stages

For **`zwischen_finalize`**:

- `00_eval_setup.pt` — eval group labels, clean/noisy labels, dataset indices
- `05_signal_table.pt` — per-sample uncertainty signals

Optional (used when building `results.pt`):

- `01_deterministic_forward.pt` or `04_mc_dropout.pt` — `mean_prediction` tensor

Stages before `05` that are missing are reported as **`partial`** only; they are not rebuilt automatically.

## API

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/experiments/no-auth/recoverability` | Scan experiments (`?status=failed` optional) |
| `GET /api/v1/experiments/no-auth/{id}/recoverability` | Single-run assess |
| `POST /api/v1/experiments/no-auth/{id}/recover` | Finalize one run; sets `status=completed`, clears `error_message` |
| `POST /api/v1/experiments/no-auth/recover-batch` | Body: `{status, tier}` — batch recover |

Backend service: `backend/app/services/run_recovery_service.py`.

## Streamlit UI

In **Results · §1 Live status**, **Bulk recover** (next to bulk delete):

- Shows counts: failed · recoverable from zwischen · DB sync only
- **Recover N failed (extract results)** → `recover-batch` with `tier=zwischen_finalize`
- **Sync K completed metrics to DB** → `tier=db_sync` when applicable

Toggle: **Results · bulk recover** in UI debug (`results_bulk_recover`).

## Example: Jun 22 `mutual_info` batch

Fifteen fast-pilot runs failed with `Training failed: 'mutual_info'` after `05_signal_table.pt` was written (`dropout=0` omitted `mutual_info` from the signal table). Each run is **`zwischen_finalize`**:

```bash
curl -s 'http://localhost:8000/api/v1/experiments/no-auth/recoverability?status=failed'
curl -X POST 'http://localhost:8000/api/v1/experiments/no-auth/recover-batch' \
  -H 'Content-Type: application/json' \
  -d '{"status":"failed","tier":"zwischen_finalize"}'
```

After recovery, expect `summary.json`, `results.pt`, `per_sample_signals.csv`, and API `status=completed` with non-null AUROC fields.

## Out of scope

- Re-training or `checkpoint.pt` resume
- Rebuilding incomplete `zwischen` chains (reported as `partial` only)
