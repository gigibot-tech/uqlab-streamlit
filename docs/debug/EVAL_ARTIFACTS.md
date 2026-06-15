# Debug one experiment run

## Streamlit (simplified)

| Tab | Purpose |
|-----|---------|
| **Hypothesis Validation** | Preset sweeps → `results/validation/` → plots + inspect one folder |
| **Custom experiments (API)** | Same preset sweeps + optional custom API grids |
| **Tools** | Model selector, UQ benchmarks |

Config for preset sweeps: `src/walaris/validation_config.py` (single YAML schema).

Runner: `scripts/run_validation_experiments.py` → `run_fast_uncertainty_classification.py`.

---

# Debug one experiment run

## What one run produces

After `scripts/run_fast_uncertainty_classification.py` finishes, the output folder contains:

| File | Use it to check |
|------|----------------|
| `summary.json` | Eval group sizes, one-vs-rest AUROC per signal, config |
| `per_sample_signals.csv` | Which samples were clean / aleatoric / epistemic and their signal values |
| `results.pt` | Same evaluation in tensor form (used to rebuild `metrics.csv`) |

Hypothesis Validation plots read **`results/validation/<sweep>/metrics.csv`**, which is built from many run folders via `scripts/run_validation_experiments.py`.

The FastAPI / batch UI reads **`summary.json`** per experiment.

## Provenance (short)

```text
sample_indices_for_fast_pilot  →  3 eval index lists
run_fast_uncertainty_classification  →  signal_table + AUROC
  →  per_sample_signals.csv
  →  summary.json
  →  results.pt
```

## Python helper (one loader)

```python
from pathlib import Path
from walaris.run_artifacts import load_run_directory, load_per_sample_table

artifacts = load_run_directory(Path("results/validation/label_noise_sweep/cnn_mcdropout_noise50"))
print(artifacts.eval_sizes)
print(artifacts.auroc_by_signal())
df = load_per_sample_table(artifacts.run_dir)
```

## Manual checklist

1. Run **one** experiment (or open one existing folder).
2. Open `summary.json` → confirm `eval_sizes` (none should be 0 unless you expect that).
3. Open `per_sample_signals.csv` → confirm `group` and `is_noisy` look right.
4. Pick one signal column → see if values differ by `group`.
5. Match AUROC in `summary.json` → `one_vs_rest_auroc` for that signal.
6. Only then open Streamlit / batch heatmaps.

Do **not** start debugging from Streamlit plots.

## Rebuild sweep CSV from disk

```bash
python scripts/run_validation_experiments.py --rebuild-only
```
