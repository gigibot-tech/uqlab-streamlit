# UQLab Flask UI

Lean Flask shell over the existing uqlab runner (`uqlab.runner.execute.run_from_yaml`).

## Patterns (see `src/uqlab/runner/patterns.py`)

- **Pipeline** — load config → validate → execute
- **Factory** — `build_model()` picks classifier by architecture
- **Strategy** — signal families (predictive / logit / attribution)

## Run

```bash
cd uqlab-streamlit
pip install -r uqlab-flask/requirements.txt
PYTHONPATH=src:uqlab-flask python uqlab-flask/app.py
```

Open http://127.0.0.1:5001 — 5-step wizard, one **Launch** runs the full sweep sequentially.

After launch you land on `/sweep/<group_id>` (bookmarkable). Status auto-polls every 3s; **Refresh status** re-fetches without re-launching.

**3-line sweep plot** (modular signal picker):
- `GET /sweep/<group_id>/plot?signal=inverse_coherence`
- Left Y: `{signal}_mean_epistemic` / `{signal}_mean_aleatoric` (raw signal, not AUROC)
- Right Y: accuracy · X: `noise_percent` or `under_train_per_class`
- Default signal: `inverse_coherence` (label-noise) or `inverse_mass` (dataset-size) — see `sweep_line_plot.py`

Safeguards:
- POST → redirect → GET (browser refresh does not spawn a new sweep)
- One-time launch token (double-click safe)
- Same workflow cannot start a duplicate sweep while one is active
- Single background worker runs all 5 jobs in one batch
