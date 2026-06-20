# Signal registry (EK-FAK)

Fast-pilot uncertainty signals use a **sources → primitives → metrics** pipeline.

- **Sources** ([`sources.py`](../../src/uqlab/evaluation/signals/sources.py)): run only what enabled metrics need.
- **Primitives** ([`primitives.py`](../../src/uqlab/evaluation/signals/primitives.py)): `dict[str, Tensor]` with dotted keys (`forward.det_logits`, `attribution.coherence`, …).
- **Metrics** ([`registry.py`](../../src/uqlab/evaluation/signals/registry.py)): `METRICS` dict of `MetricEntry` — each metric is a small `compute(store)` function.

[`formulas.py`](../../src/uqlab/evaluation/signals/formulas.py) remains the **audit manifest** (provenance for runs); runtime does not execute the formula DAG.

Legacy `SignalCalculator` lives in [`archive/legacy_src/evaluation/signal_calculator.py`](../../archive/legacy_src/evaluation/signal_calculator.py).

## Pipeline

```
run_sources(needed) → PrimitiveStore → METRICS[id].compute(store) → per_sample_signals.csv
```

`collect_uncertainty_signals` unions `sources` for enabled metrics, runs those sources once, then evaluates metrics.

## Source requirements

| Source | When needed | Constraints |
|--------|-------------|---------------|
| `deterministic_forward` | logit metrics | — |
| `mc_dropout` | predictive metrics | `mc_passes >= 1` |
| `attribution` | attribution / inverse_mass | method from `evaluation.attribution_method` |

`mutual_info` has `min_dropout > 0` on its `MetricEntry` — pruned when `dropout=0`.

## Plug-in: new metric

One entry in `METRICS`:

```python
"my_score": MetricEntry(
    id="my_score",
    family="attribution",
    label="My Score",
    sources=("attribution",),
    compute=lambda p: reciprocal_uncertainty(p["attribution.mass"]),
    epistemic=True,
),
```

UI, Step 4, and YAML families pick it up automatically via `signal_names()`.

## Plug-in: new attribution method

One function + one line in `ATTRIBUTION_METHODS`:

```python
def ig_primitives(ctx: EvalContext) -> PrimitiveStore:
    return {
        "attribution.coherence": coherence,
        "attribution.mass": mass,
        "attribution.dominance": dominance,
    }

ATTRIBUTION_METHODS["integrated_gradients"] = ig_primitives
```

Set `evaluation.attribution_method: integrated_gradients` in run YAML. Metrics reading `attribution.*` primitives work unchanged.

## Canonical metrics

| Metric | Sources | Notes |
|--------|---------|-------|
| `msp_uncertainty` | `mc_dropout` | `1 - max(mc.mean_prediction)` |
| `predictive_entropy` | `mc_dropout` | `mc.entropy` |
| `mutual_info` | `mc_dropout` | `mc.mutual_info`; pruned if `dropout=0` |
| `inverse_coherence` | `attribution` | `1 - attribution.coherence` |
| `inverse_dominance` | `attribution` | `1 - attribution.dominance` |
| `inverse_mass` | `attribution` | `1 / (attribution.mass + ε)` |
| `inverse_logit_magnitude` | `deterministic_forward` | `1 / (|logit_pred| + ε)` |

## Config

- Step 4 `selected_signals` → `evaluation.signals` via `signals_from_flat_list`.
- `prune_signals_for_runtime` uses `metric_runtime_ok` per metric.
- `run_experiment_core` passes `enabled_signals`, `dropout`, and `attribution_method` into `collect_uncertainty_signals`.
