# Registries

Where named knobs are defined and how they connect to runs.

**Experiment flow:** [`docs/UQLAB_FLOW.md`](../UQLAB_FLOW.md)

## `METRICS` — uncertainty signals

**File:** [`src/uqlab/evaluation/signals/registry.py`](../../src/uqlab/evaluation/signals/registry.py)

| ID | Family | Aleatoric | Epistemic | Source |
|----|--------|-----------|-----------|--------|
| `predictive_entropy` | predictive | | | `mc_dropout` — H[mean(p)] |
| `expected_entropy` | predictive | yes | | `mc_dropout` — E[H(p)] (paper aleatoric) |
| `mutual_info` | predictive | | yes | `mc_dropout` — H − E[H] (paper epistemic) |
| `inverse_coherence` | attribution | yes | | `attribution` |
| `inverse_mass` | logit | | yes | `attribution` |
| … | | | | see registry |

**Plug-in path:** `run_sources` → `PrimitiveStore` → `METRICS[id].compute` → `signal_table` in `results.pt`.

Detail: [`signal-registry.md`](signal-registry.md)

## `SOURCE_REGISTRY` — computation backends

**File:** [`src/uqlab/evaluation/signals/sources.py`](../../src/uqlab/evaluation/signals/sources.py)

| Source | Provides |
|--------|----------|
| `deterministic_forward` | `forward.det_logits`, `forward.mean_pred` |
| `mc_dropout` | `mc.entropy`, `mc.mutual_info`, `mc.mean_prediction` |
| `attribution` | DualXDA coherence / mass / dominance |

## `UNCERTAINTY_PERSPECTIVES` — sweep types (UI / launch)

**Package:** [`src/uqlab_orchestrator/uncertainty/`](../../src/uqlab_orchestrator/uncertainty/)

Drives Step 5 launch buttons: label-noise (aleatoric axis) vs under-train / dataset size (epistemic axis). `resolve_launch_actions` builds primary + mirror sweep arms.

## `ModelRegistry` — architectures

**File:** [`src/uqlab/models/architectures.py`](../../src/uqlab/models/architectures.py)

Maps `model_architecture` YAML values to trainable backbones + heads (ResNet, DINOv2, DualXDA, …).
