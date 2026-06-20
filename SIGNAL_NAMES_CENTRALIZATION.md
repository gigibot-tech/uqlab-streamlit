# Signal Names Centralization

**Updated**: 2026-06-20  
**Status**: Complete (Phase 4)

## Single source of truth

All **exported** fast-pilot metrics are defined once in:

| Layer | Module | What to import |
|-------|--------|----------------|
| **Registry (authoritative)** | `uqlab.evaluation.signals.registry` | `METRICS`, `signal_names()`, `signal_labels()`, `signals_by_family()`, `epistemic_signal_ids()`, `aleatoric_signal_ids()` |
| **App constants (derived)** | `uqlab.shared.types` | `SIGNAL_NAMES`, `SIGNAL_LABELS`, `EPISTEMIC_SIGNALS`, `ALEATORIC_SIGNALS`, `signal_choices()`, `signals_viz_categories()` |
| **Run artifacts** | `uqlab.run_artifacts` | `FAST_PILOT_SIGNAL_NAMES` (= `tuple(signal_names())`) |
| **Config / YAML** | `uqlab.shared.config.signals` | `normalize_evaluation_signals`, `validate_evaluation_signals`, `SIGNAL_ID_ALIASES` |

See also: [`docs/features/signal-registry.md`](docs/features/signal-registry.md) (EK-FAK plug-in cookbook).

## Canonical 7 metrics

```text
msp_uncertainty
predictive_entropy
mutual_info
inverse_coherence
inverse_dominance      ← exported metric (1 − raw top-k dominance)
inverse_mass
inverse_logit_magnitude
```

**Config alias**: YAML / Step 4 may still say `dominance`; `SIGNAL_ID_ALIASES` maps it → `inverse_dominance`.

**Internal primitives** (not exported in `per_sample_signals.csv`): raw `coherence` and `dominance` tensors inside attribution sources (`attribution.py`, `primitives.py`). Do not add these to UI pickers.

**Legacy CSV columns**: pre-refactor runs may have `coherence` / `dominance` columns. `LEGACY_SIGNAL_NAMES` in `shared/types.py` lets viz code show them when present.

## Where lists are derived (not hardcoded)

| Consumer | Import |
|----------|--------|
| Step 4 / experiment config | `signal_names()` |
| `results_io.py`, `notebook_utils/signals.py` | `signal_names()` |
| `run_artifacts.FAST_PILOT_SIGNAL_NAMES` | `signal_names()` |
| `uq_benchmarks.py`, `benchmarks/visualization.py` | `SIGNAL_NAMES` |
| `heatmap_visualization.py` | `signal_choices()`, `EPISTEMIC_SIGNALS`, `ALEATORIC_SIGNALS` |
| `signal_visualization.py` | `signals_viz_categories()` |
| `per_sample_signals_viz.py` | `SIGNAL_NAMES` + `LEGACY_SIGNAL_NAMES` |
| `notebook_utils/constants.UNCERTAINTY_SIGNALS` | `SIGNAL_LABELS` |

## Adding a new metric

1. Add one `MetricEntry` to `METRICS` in `registry.py` (sources + `compute`).
2. Optionally extend `formulas.py` for audit provenance.
3. **Do not** add a parallel list in viz/UI — `SIGNAL_NAMES` updates automatically.
4. Add tests in `tests/test_runner_signals.py`.

## Legacy / out of scope

- `archive/legacy_src/evaluation/signal_calculator.py` — archived; import raises `ImportError`.
- `evaluation/legacy/**` — triage / DualXDA axioms still reference raw `dominance` internally.
- `scripts/legacy/**` — historical analysis scripts; not on the hot path.

## Verification

```bash
# No hardcoded 7-signal lists in active UI (except registry/types)
rg "'dominance'" src/uqlab/ui_components src/uqlab/shared/types.py

# Registry is the definition
PYTHONPATH=src python -c "from uqlab.evaluation.signals.registry import signal_names; print(signal_names())"
```

Expected `signal_names()` output: 7 ids ending with `inverse_dominance`, not `dominance`.
