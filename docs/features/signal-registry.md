# Signal registry (EK-FAK pipeline)

Fast-pilot uncertainty signals use a **sources → primitives → metrics** pipeline named **EK-FAK** in code (the registry module docstring). That is the **metrics pipeline name**, not a DA method.

DA backends that feed attribution metrics:

- **DualXDA** → `dualxda.*` primitives → `inverse_*_dualxda` metrics
- **EK-FAC / Kronfluence** → `ek_fak.*` primitives → `inverse_*_ek_fak` metrics

- **Sources** ([`sources.py`](../../src/uqlab/evaluation/signals/sources.py)): run only what enabled metrics need.
- **Primitives** ([`primitives.py`](../../src/uqlab/evaluation/signals/primitives.py)): `dict[str, Tensor]` with dotted keys (`forward.det_logits`, `dualxda.coherence`, `ek_fak.mass`, …).
- **Metrics** ([`registry.py`](../../src/uqlab/evaluation/signals/registry.py)): `METRICS` dict of `MetricEntry` — each metric is a small `compute(store)` function.

[`formulas.py`](../../src/uqlab/evaluation/signals/formulas.py) remains the **audit manifest** (provenance for runs); runtime does not execute the formula DAG.

Legacy `SignalCalculator` lives in [`archive/legacy_src/evaluation/signal_calculator.py`](../../archive/legacy_src/evaluation/signal_calculator.py).

## Evaluation loops

See [`docs/UQLAB_FLOW.md`](../../docs/UQLAB_FLOW.md#evaluation-loops-one-job-many-consumers) for the full diagram. Short version:

| Loop | Function | Iterates |
|------|----------|----------|
| Job | ``collect_uncertainty_signals`` | ``enabled_signals`` → sources → ``METRICS[id].compute`` |
| AUROC / CSV | ``score_uncertainty_signals`` | **each** ``signal_table`` column |
| Sweep plots | ``sweep_line_plot`` | **each** plottable registry signal (``FAST_PILOT_SIGNAL_NAMES``) |
| Disentanglement | ``predict_disentangling`` | **one** aleatoric + epistemic pair; ``score_bridge_pairs_from_results`` loops presets |

DA backends (DualXDA / EK-FAC) are inferred from enabled metrics via ``derive_attribution_backends_from_signals`` — no separate runtime default.

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
| `attribution_dualxda` | `inverse_*_dualxda` | DualXDA tracer |
| `attribution_ek_fak` | `inverse_*_ek_fak` | Kronfluence (`pip install kronfluence` or `uv sync --extra ek_fak`) |
| `attribution` | legacy alias | same as `attribution_dualxda` |

`mutual_info` has `min_dropout > 0` on its `MetricEntry` — pruned when `dropout=0`.

Enable both backends in one job:

```yaml
evaluation:
  attribution_backends: [dualxda, ek_fak]
  signals:
    attribution:
      - inverse_coherence_dualxda
      - inverse_mass_dualxda
      - inverse_coherence_ek_fak
      - inverse_mass_ek_fak
```

## Plug-in: new metric

One entry in `METRICS`:

```python
"my_score": MetricEntry(
    id="my_score",
    family="attribution",
    label="My Score",
    sources=("attribution_dualxda",),
    compute=lambda p: reciprocal_uncertainty(p["dualxda.mass"]),
    epistemic=True,
),
```

UI, Step 4, and YAML families pick it up automatically via `signal_names()`.

## Plug-in: new attribution backend

One function + one line in `ATTRIBUTION_METHODS` and `SOURCE_REGISTRY`:

```python
def ig_primitives(ctx: EvalContext) -> PrimitiveStore:
    return namespaced_attribution_store("integrated_gradients", coherence, mass, dominance)

ATTRIBUTION_METHODS["integrated_gradients"] = ig_primitives
```

Set `evaluation.attribution_backends: [integrated_gradients]` in run YAML.

## Canonical metrics

Shared catalog (display names, bridge presets, ``predict_disentangling`` notes):
[`shared/config/signals.py`](../../src/uqlab/shared/config/signals.py) — ``SIGNAL_CATALOG``, ``DISENTANGLING_BRIDGE_PRESETS``, ``PREDICT_DISENTANGLING_NOTE``.

| Metric | Sources | Tag | Aleatoric / epistemic | Notes |
|--------|---------|-----|----------------------|-------|
| `msp_uncertainty` | `mc_dropout` | Information-theoretic · MC dropout | — | `1 - max(mc.mean_prediction)` |
| `predictive_entropy` | `mc_dropout` | Information-theoretic · MC dropout | — | `mc.entropy` |
| `mutual_info` | `mc_dropout` | Information-theoretic · MC dropout | epistemic | pruned if `dropout=0` |
| `expected_entropy` | `mc_dropout` | Information-theoretic · MC dropout | aleatoric | paper bridge aleatoric |
| `inverse_coherence_dualxda` | `attribution_dualxda` | DualXDA | aleatoric | `1 - dualxda.coherence` |
| `inverse_dominance_dualxda` | `attribution_dualxda` | DualXDA | epistemic | `1 - dualxda.dominance` |
| `inverse_mass_dualxda` | `attribution_dualxda` | DualXDA | epistemic | signal_dualxda bridge epistemic |
| `inverse_coherence_ek_fak` | `attribution_ek_fak` | EK-FAC | aleatoric | `1 - ek_fak.coherence` |
| `inverse_dominance_ek_fak` | `attribution_ek_fak` | EK-FAC | epistemic | `1 - ek_fak.dominance` |
| `inverse_mass_ek_fak` | `attribution_ek_fak` | EK-FAC | epistemic | signal_ek_fak bridge epistemic |
| `inverse_logit_magnitude` | `deterministic_forward` | Representer logit | epistemic | `1 / (|logit_pred| + ε)` |

Legacy ids `inverse_coherence`, `inverse_mass`, `inverse_dominance` alias to `*_dualxda`.

Upstream Keras mapping → [`docs/UQLAB_FLOW.md`](../../docs/UQLAB_FLOW.md#paper-vs-signal-pairing-bridge-defaults).

## Config

- Step 4 `selected_signals` → `evaluation.signals` via `signals_from_flat_list`.
- `prune_signals_for_runtime` uses `metric_runtime_ok` per metric.
- `run_experiment_core` builds ``EvalSignalConfig.from_run_config(run_cfg, ...)`` and passes it to ``collect_uncertainty_signals``.
