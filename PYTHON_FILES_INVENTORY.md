# Python Files Inventory - walaris-cen

**Generated**: 2026-06-08  
**Total Python Files**: 150

## Package Structure

```
walaris-cen/
├── src/
│   ├── uqlab/                    # ML Core Package (Steps 1-7 MLOps pipeline)
│   └── uqlab_orchestrator/       # Orchestration Package (Experiment coordination)
```

## src/uqlab/ - ML Core Package

### Root Level
- src/uqlab/__init__.py
- src/uqlab/experiment_config_flat.py
- src/uqlab/experiment_discovery.py
- src/uqlab/mc_dropout_uq.py
- src/uqlab/results_io.py
- src/uqlab/run_artifacts.py
- src/uqlab/runtime_paths.py

### 1_data/ - Data Loading & Preprocessing
- src/uqlab/1_data/__init__.py
- src/uqlab/1_data/loaders.py
- src/uqlab/1_data/preprocessing.py
- src/uqlab/1_data/stats.py

### 2_models/ - Model Architectures
- src/uqlab/2_models/__init__.py
- src/uqlab/2_models/architectures.py
- src/uqlab/2_models/classification_models.py
- src/uqlab/2_models/factory.py
- src/uqlab/2_models/feature_extractors.py
- src/uqlab/2_models/uncertainty.py

### 3_training/ - Training Logic
- src/uqlab/3_training/__init__.py
- src/uqlab/3_training/callbacks.py
- src/uqlab/3_training/config.py
- src/uqlab/3_training/trainer.py

### 4_evaluation/ - Evaluation & Signals
- src/uqlab/4_evaluation/__init__.py
- src/uqlab/4_evaluation/benchmarks/__init__.py
- src/uqlab/4_evaluation/benchmarks/data/__init__.py
- src/uqlab/4_evaluation/benchmarks/data/cifar10.py
- src/uqlab/4_evaluation/benchmarks/datatypes.py
- src/uqlab/4_evaluation/benchmarks/examples/basic_usage.py
- src/uqlab/4_evaluation/benchmarks/examples/visualization_example.py
- src/uqlab/4_evaluation/benchmarks/implementations/__init__.py
- src/uqlab/4_evaluation/benchmarks/models/__init__.py
- src/uqlab/4_evaluation/benchmarks/models/base.py
- src/uqlab/4_evaluation/benchmarks/models/gaussian_logits.py
- src/uqlab/4_evaluation/benchmarks/setup.py
- src/uqlab/4_evaluation/benchmarks/utils/__init__.py
- src/uqlab/4_evaluation/benchmarks/visualization.py
- src/uqlab/4_evaluation/evaluator.py
- src/uqlab/4_evaluation/metrics.py
- src/uqlab/4_evaluation/signals.py
- src/uqlab/4_evaluation/signals/__init__.py
- src/uqlab/4_evaluation/signals/attribution.py
- src/uqlab/4_evaluation/signals/formulas.py
- src/uqlab/4_evaluation/validators.py

### 5_api/ - API Integration
- src/uqlab/5_api/__init__.py
- src/uqlab/5_api/batch.py
- src/uqlab/5_api/datasets.py
- src/uqlab/5_api/experiments.py
- src/uqlab/5_api/integrations/__init__.py
- src/uqlab/5_api/integrations/watsonx.py
- src/uqlab/5_api/models.py

### 7_orchestration/ - Orchestration Logic
- src/uqlab/7_orchestration/__init__.py
- src/uqlab/7_orchestration/batch_runner.py
- src/uqlab/7_orchestration/checkpoints_legacy.py
- src/uqlab/7_orchestration/experiment_runner.py
- src/uqlab/7_orchestration/storage.py

### backbones/ - Model Backbones
- src/uqlab/backbones/__init__.py
- src/uqlab/backbones/baseline_models.py
- src/uqlab/backbones/dinov2_backbone.py
- src/uqlab/backbones/heteroscedastic_mc_dropout.py
- src/uqlab/backbones/imagenet_baselines.py
- src/uqlab/backbones/load_dinov2_model.py
- src/uqlab/backbones/mc_dropout_model.py

### benchmarks/ - Benchmarking
- src/uqlab/benchmarks/__init__.py

### classification/ - Classification Tasks
- src/uqlab/classification/__init__.py
- src/uqlab/classification/attribution_signals.py
- src/uqlab/classification/config.py
- src/uqlab/classification/data_loader.py
- src/uqlab/classification/evaluation.py
- src/uqlab/classification/feature_extractor.py
- src/uqlab/classification/hydra_wrapper.py
- src/uqlab/classification/model_factory.py
- src/uqlab/classification/models.py
- src/uqlab/classification/signal_formula_specs.py
- src/uqlab/classification/utils.py
- src/uqlab/classification/watsonx_streamlit.py

### data_loaders/ - Data Loaders
- src/uqlab/data_loaders/__init__.py
- src/uqlab/data_loaders/cifar10_loader.py
- src/uqlab/data_loaders/cifar10n_loader.py
- src/uqlab/data_loaders/dinov2_transforms.py
- src/uqlab/data_loaders/svhn_loader.py

### legacy_experiments/ - Legacy Experiments
- src/uqlab/legacy_experiments/__init__.py
- src/uqlab/legacy_experiments/dualxda_stream.py
- src/uqlab/legacy_experiments/risk_coverage_report.py

### legacy_metrics/ - Legacy Metrics
- src/uqlab/legacy_metrics/__init__.py
- src/uqlab/legacy_metrics/acquisition_functions.py
- src/uqlab/legacy_metrics/integrity_score.py
- src/uqlab/legacy_metrics/standard_uq_metrics.py
- src/uqlab/legacy_metrics/surgical_score.py
- src/uqlab/legacy_metrics/uncertainty_suite.py

### notebook_support/ - Notebook Utilities
- src/uqlab/notebook_support/__init__.py
- src/uqlab/notebook_support/method_comparison_plotly.py
- src/uqlab/notebook_support/metric_specs.py
- src/uqlab/notebook_support/signals.py

### shared/ - Shared Utilities
- src/uqlab/shared/__init__.py
- src/uqlab/shared/config/__init__.py
- src/uqlab/shared/config/classification.py
- src/uqlab/shared/config/global_config.py
- src/uqlab/shared/config/schemas.py
- src/uqlab/shared/config/workflow_validation.py
- src/uqlab/shared/notebook_utils/__init__.py
- src/uqlab/shared/notebook_utils/comparisons/__init__.py
- src/uqlab/shared/notebook_utils/comparisons/method_comparison_plotly.py
- src/uqlab/shared/notebook_utils/comparisons/method_comparison.py
- src/uqlab/shared/notebook_utils/comparisons/metric_specs.py
- src/uqlab/shared/notebook_utils/comparisons/single_architecture_plot.py
- src/uqlab/shared/notebook_utils/constants.py
- src/uqlab/shared/notebook_utils/data_utils.py
- src/uqlab/shared/notebook_utils/metrics.py
- src/uqlab/shared/notebook_utils/plotting.py
- src/uqlab/shared/notebook_utils/signals.py
- src/uqlab/shared/types.py
- src/uqlab/shared/utils/__init__.py
- src/uqlab/shared/utils/classification.py
- src/uqlab/shared/utils/core.py
- src/uqlab/shared/utils/tracking.py

### triage/ - Triage & Debugging
- src/uqlab/triage/dualxda_axioms.py

### ui_components/ - UI Components (Streamlit)
- src/uqlab/ui_components/__init__.py
- src/uqlab/ui_components/config_types.py
- src/uqlab/ui_components/correlation_analysis.py
- src/uqlab/ui_components/data_overlap_analysis.py
- src/uqlab/ui_components/dataset.py
- src/uqlab/ui_components/experiment_config.py
- src/uqlab/ui_components/experiment_validation.py
- src/uqlab/ui_components/heatmap_visualization.py
- src/uqlab/ui_components/hypothesis_validation.py
- src/uqlab/ui_components/legacy/__init__.py
- src/uqlab/ui_components/legacy/batch_2d_sweep.py
- src/uqlab/ui_components/legacy/batch_config.py
- src/uqlab/ui_components/model_selector.py
- src/uqlab/ui_components/per_sample_signals_viz.py
- src/uqlab/ui_components/results.py
- src/uqlab/ui_components/signal_diagnostic_viz.py
- src/uqlab/ui_components/signal_visualization.py
- src/uqlab/ui_components/unified_builder.py
- src/uqlab/ui_components/uq_benchmarks.py
- src/uqlab/ui_components/utils.py
- src/uqlab/ui_components/validation_runner.py
- src/uqlab/ui_components/validation_visualization.py

## src/uqlab_orchestrator/ - Orchestration Package

### Root Level
- src/uqlab_orchestrator/__init__.py
- src/uqlab_orchestrator/api_client.py
- src/uqlab_orchestrator/experiment_config.py

### config/ - Configuration
- src/uqlab_orchestrator/config/__init__.py
- src/uqlab_orchestrator/config/validation_config.py

### sweeps/ - Sweep Generation
- src/uqlab_orchestrator/sweeps/__init__.py
