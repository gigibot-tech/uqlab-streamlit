# `evaluation/classification` removed

This directory previously held the legacy ``uq_classification`` package: shims plus
misplaced training/data code.

## Where imports went

| Old | New |
|-----|-----|
| `evaluation.classification.config` | `uqlab.shared.config.classification` |
| `evaluation.classification.models` | `uqlab.models.classification_models` |
| `evaluation.classification.model_factory` | `uqlab.models.factory` |
| `evaluation.classification.data_loader` | `uqlab.data.fast_pilot_loader` |
| `evaluation.classification.image_dataset` | `uqlab.data.image_dataset` |
| `evaluation.classification.benchmark_axes` | `uqlab.data.benchmark_axes` |
| `evaluation.classification.pipeline.*` | `uqlab.evaluation.pipeline.*` |
| `evaluation.classification.evaluation` | `uqlab.evaluation.metrics` + `uqlab.evaluation.result_writers` |
| `evaluation.classification.watsonx_*` | `uqlab.evaluation.exports.*` / `ui_components.integrations.watsonx` |
| `uqlab.api` REST routers | `backend/app/api/routes/` (archived copies in `dead_code/api/`) |
| `hydra_wrapper` | `dead_code/evaluation/hydra_wrapper.py` (optional) |

See [IMPORT_GUIDE.md](../../../IMPORT_GUIDE.md) for the full map.
