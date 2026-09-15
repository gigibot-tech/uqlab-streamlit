# Component Index

**Generated**: Fri Jun 19 14:08:19 CEST 2026  
**Project**: uqlab-streamlit

## Overview

This index catalogs all CamelCase components in the project, their usage patterns, and reuse opportunities.

## Configuration Classes

| Component | Location | Files Using | Reuse |
|-----------|----------|-------------|-------|
| [`AleatoricConfig`](./AleatoricConfig.md) | `src/uqlab/ui_components/config/config_types.py:64` | 0 | ⚠️ Low |
| [`BatchExperimentConfig`](./BatchExperimentConfig.md) | `src/uqlab/api/batch.py:31` | 0 | ⚠️ Low |
| [`CheckpointConfig`](./CheckpointConfig.md) | `src/uqlab/training/config.py:100` | 0 | ⚠️ Low |
| [`ConfigValidator`](./ConfigValidator.md) | `src/uqlab/evaluation/validators.py:22` | 0 | ⚠️ Low |
| [`DataConfig`](./DataConfig.md) | `src/uqlab/shared/config/classification.py:72` | 0 | ⚠️ Low |
| [`EarlyStoppingConfig`](./EarlyStoppingConfig.md) | `src/uqlab/training/config.py:124` | 0 | ⚠️ Low |
| [`EpistemicConfig`](./EpistemicConfig.md) | `src/uqlab/ui_components/config/config_types.py:55` | 0 | ⚠️ Low |
| [`EvaluationConfig`](./EvaluationConfig.md) | `src/uqlab/shared/config/classification.py:143` | 0 | ⚠️ Low |
| [`ExperimentConfig`](./ExperimentConfig.md) | `src/uqlab/shared/config/classification.py:165` | 7 | ✅ High |
| [`GlobalConfig`](./GlobalConfig.md) | `src/uqlab/shared/config/global_config.py:240` | 0 | ⚠️ Low |
| [`ModelConfig`](./ModelConfig.md) | `src/uqlab/shared/config/classification.py:87` | 3 | ✅ High |
| [`OptimizerConfig`](./OptimizerConfig.md) | `src/uqlab/training/config.py:22` | 0 | ⚠️ Low |
| [`PathConfig`](./PathConfig.md) | `src/uqlab/shared/config/classification.py:150` | 0 | ⚠️ Low |
| [`PathsConfig`](./PathsConfig.md) | `src/uqlab/shared/config/schemas.py:158` | 0 | ⚠️ Low |
| [`RegularizationConfig`](./RegularizationConfig.md) | `src/uqlab/training/config.py:77` | 0 | ⚠️ Low |
| [`SchedulerConfig`](./SchedulerConfig.md) | `src/uqlab/training/config.py:47` | 0 | ⚠️ Low |
| [`SweepConfig`](./SweepConfig.md) | `src/uqlab/ui_components/config/config_types.py:43` | 0 | ⚠️ Low |
| [`SystemConfig`](./SystemConfig.md) | `src/uqlab/shared/config/global_config.py:209` | 0 | ⚠️ Low |
| [`TrainingConfig`](./TrainingConfig.md) | `src/uqlab/training/config.py:143` | 3 | ✅ High |
| [`UnifiedBuilderConfig`](./UnifiedBuilderConfig.md) | `src/uqlab/ui_components/config/config_types.py:72` | 0 | ⚠️ Low |
| [`ValidationConfig`](./ValidationConfig.md) | `src/uqlab/ui_components/config/config_types.py:21` | 1 | ⚠️ Low |
| [`WorkflowConfig`](./WorkflowConfig.md) | `src/uqlab/shared/config/workflow_validation.py:211` | 0 | ⚠️ Low |
| [`WorkflowDatasetConfig`](./WorkflowDatasetConfig.md) | `src/uqlab/shared/config/workflow_validation.py:32` | 0 | ⚠️ Low |
| [`WorkflowEvaluationConfig`](./WorkflowEvaluationConfig.md) | `src/uqlab/shared/config/workflow_validation.py:184` | 0 | ⚠️ Low |
| [`WorkflowTrainingConfig`](./WorkflowTrainingConfig.md) | `src/uqlab/shared/config/workflow_validation.py:77` | 0 | ⚠️ Low |
| [`WorkflowUncertaintyConfig`](./WorkflowUncertaintyConfig.md) | `src/uqlab/shared/config/workflow_validation.py:118` | 0 | ⚠️ Low |

## Coordinator Classes

| Component | Location | Files Using | Reuse |
|-----------|----------|-------------|-------|

## Other Components

| Component | Location | Files Using | Reuse |
|-----------|----------|-------------|-------|
| [`AcquisitionFunction`](./AcquisitionFunction.md) | `src/uqlab/evaluation/legacy/metrics/acquisition_functions.py:19` | 0 | ⚠️ Low |
| [`AsyncBatchRunner`](./AsyncBatchRunner.md) | `src/uqlab/orchestration/batch_runner.py:234` | 0 | ⚠️ Low |
| [`AxiomThresholds`](./AxiomThresholds.md) | `src/uqlab/evaluation/legacy/triage/dualxda_axioms.py:37` | 2 | ⚠️ Low |
| [`BALDAcquisition`](./BALDAcquisition.md) | `src/uqlab/evaluation/legacy/metrics/acquisition_functions.py:213` | 0 | ⚠️ Low |
| [`BaselineResNet18`](./BaselineResNet18.md) | `src/uqlab/models/backbones/baseline_models.py:121` | 0 | ⚠️ Low |
| [`BaselineResNet50`](./BaselineResNet50.md) | `src/uqlab/models/backbones/baseline_models.py:69` | 0 | ⚠️ Low |
| [`BaselineVGG16`](./BaselineVGG16.md) | `src/uqlab/models/backbones/baseline_models.py:16` | 0 | ⚠️ Low |
| [`BatchContext`](./BatchContext.md) | `src/uqlab/orchestration/batch_runner.py:43` | 0 | ⚠️ Low |
| [`BatchCreate`](./BatchCreate.md) | `src/uqlab/api/batch.py:38` | 0 | ⚠️ Low |
| [`BatchExperimentSummary`](./BatchExperimentSummary.md) | `src/uqlab/api/batch.py:59` | 0 | ⚠️ Low |
| [`BatchGenerator`](./BatchGenerator.md) | `src/uqlab_orchestrator/batch/generator.py:28` | 2 | ⚠️ Low |
| [`BatchListResponse`](./BatchListResponse.md) | `src/uqlab/api/batch.py:86` | 0 | ⚠️ Low |
| [`BatchOrchestrator`](./BatchOrchestrator.md) | `src/uqlab_orchestrator/batch/orchestrator.py:16` | 1 | ⚠️ Low |
| [`BatchResponse`](./BatchResponse.md) | `src/uqlab/api/batch.py:70` | 0 | ⚠️ Low |
| [`BatchRunner`](./BatchRunner.md) | `src/uqlab/orchestration/batch_runner.py:59` | 0 | ⚠️ Low |
| [`BatchStatus`](./BatchStatus.md) | `src/uqlab/orchestration/batch_runner.py:33` | 0 | ⚠️ Low |
| [`BatchUpdateRequest`](./BatchUpdateRequest.md) | `src/uqlab/api/batch.py:98` | 0 | ⚠️ Low |
| [`Callback`](./Callback.md) | `src/uqlab/training/callbacks.py:25` | 1 | ⚠️ Low |
| [`CallbackList`](./CallbackList.md) | `src/uqlab/training/callbacks.py:363` | 1 | ⚠️ Low |
| [`CallbackProtocol`](./CallbackProtocol.md) | `src/uqlab/shared/types.py:173` | 0 | ⚠️ Low |
| [`CheckpointCallback`](./CheckpointCallback.md) | `src/uqlab/training/callbacks.py:61` | 0 | ⚠️ Low |
| [`CheckpointManager`](./CheckpointManager.md) | `src/uqlab/orchestration/storage.py:271` | 0 | ⚠️ Low |
| [`CIFAR10Dataset`](./CIFAR10Dataset.md) | `src/uqlab/data/loaders/cifar10_loader.py:11` | 0 | ⚠️ Low |
| [`CIFAR10NDataset`](./CIFAR10NDataset.md) | `src/uqlab/data/loaders.py:50` | 6 | ✅ High |
| [`CIFAR10NLabelView`](./CIFAR10NLabelView.md) | `src/uqlab/data/loaders.py:221` | 1 | ⚠️ Low |
| [`CIFAR10NLoader`](./CIFAR10NLoader.md) | `src/uqlab/data/loaders/cifar10n_loader.py:276` | 0 | ⚠️ Low |
| [`ClassificationDatasetProtocol`](./ClassificationDatasetProtocol.md) | `src/uqlab/data/classification_dataset.py:11` | 1 | ⚠️ Low |
| [`ClassificationModel`](./ClassificationModel.md) | `src/uqlab/models/architectures.py:223` | 0 | ⚠️ Low |
| [`CNNFeatureExtractor`](./CNNFeatureExtractor.md) | `src/uqlab/models/feature_extractors.py:177` | 0 | ⚠️ Low |
| [`CNNMCDropout`](./CNNMCDropout.md) | `src/uqlab/models/factory.py:29` | 0 | ⚠️ Low |
| [`CorrelationResult`](./CorrelationResult.md) | `src/uqlab/ui_components/visualization/analysis/correlation_analysis.py:19` | 1 | ⚠️ Low |
| [`CutMix`](./CutMix.md) | `src/uqlab/data/preprocessing.py:292` | 0 | ⚠️ Low |
| [`DataLoaderProtocol`](./DataLoaderProtocol.md) | `src/uqlab/shared/types.py:161` | 0 | ⚠️ Low |
| [`DataQualityChecker`](./DataQualityChecker.md) | `src/uqlab/evaluation/validators.py:300` | 0 | ⚠️ Low |
| [`Dataset`](./Dataset.md) | `src/uqlab/evaluation/benchmarks/datatypes.py:13` | 16 | ✅ High |
| [`DatasetSpec`](./DatasetSpec.md) | `src/uqlab/data/dataset_registry.py:26` | 0 | ⚠️ Low |
| [`DeepEnsemble`](./DeepEnsemble.md) | `src/uqlab/models/uncertainty.py:269` | 0 | ⚠️ Low |
| [`DINOv2Backbone`](./DINOv2Backbone.md) | `src/uqlab/models/backbones/dinov2_backbone.py:14` | 2 | ⚠️ Low |
| [`DINOv2FeatureExtractor`](./DINOv2FeatureExtractor.md) | `src/uqlab/models/feature_extractors.py:65` | 0 | ⚠️ Low |
| [`DINOv2WithMCDropout`](./DINOv2WithMCDropout.md) | `src/uqlab/models/backbones/dinov2_backbone.py:157` | 0 | ⚠️ Low |
| [`DropoutHead`](./DropoutHead.md) | `src/uqlab/models/architectures.py:117` | 0 | ⚠️ Low |
| [`DualXDASignalAcquisition`](./DualXDASignalAcquisition.md) | `src/uqlab/evaluation/legacy/metrics/acquisition_functions.py:251` | 0 | ⚠️ Low |
| [`DualXDATracer`](./DualXDATracer.md) | `src/uqlab/evaluation/legacy/triage/dualxda_axioms.py:368` | 3 | ✅ High |
| [`EarlyStoppingCallback`](./EarlyStoppingCallback.md) | `src/uqlab/training/callbacks.py:248` | 0 | ⚠️ Low |
| [`EmbeddingDataset`](./EmbeddingDataset.md) | `src/uqlab/models/classification_models.py:14` | 1 | ⚠️ Low |
| [`EmbeddingDropoutMLP`](./EmbeddingDropoutMLP.md) | `src/uqlab/models/classification_models.py:52` | 4 | ✅ High |
| [`EmbeddingOrganizer`](./EmbeddingOrganizer.md) | `src/uqlab_classification_backup/data_loader.py:439` | 2 | ⚠️ Low |
| [`EntropyAcquisition`](./EntropyAcquisition.md) | `src/uqlab/evaluation/legacy/metrics/acquisition_functions.py:174` | 0 | ⚠️ Low |
| [`EvaluationGroup`](./EvaluationGroup.md) | `src/uqlab/shared/types.py:193` | 0 | ⚠️ Low |
| [`ExperimentContext`](./ExperimentContext.md) | `src/uqlab/orchestration/experiment_runner.py:46` | 0 | ⚠️ Low |
| [`ExperimentCreate`](./ExperimentCreate.md) | `src/uqlab/api/experiments.py:37` | 0 | ⚠️ Low |
| [`ExperimentResponse`](./ExperimentResponse.md) | `src/uqlab/api/experiments.py:44` | 0 | ⚠️ Low |
| [`ExperimentRunner`](./ExperimentRunner.md) | `src/uqlab/orchestration/experiment_runner.py:148` | 2 | ⚠️ Low |
| [`ExperimentStatus`](./ExperimentStatus.md) | `src/uqlab/shared/types.py:124` | 0 | ⚠️ Low |
| [`ExperimentTracker`](./ExperimentTracker.md) | `src/uqlab/shared/utils/tracking.py:20` | 1 | ⚠️ Low |
| [`ExperimentVizAnalysis`](./ExperimentVizAnalysis.md) | `src/uqlab/ui_components/selectors/smart_experiment_selector.py:139` | 0 | ⚠️ Low |
| [`FeatureExtractor`](./FeatureExtractor.md) | `src/uqlab/models/feature_extractors.py:27` | 0 | ⚠️ Low |
| [`FormulaOperator`](./FormulaOperator.md) | `src/uqlab/evaluation/signals/formulas.py:25` | 0 | ⚠️ Low |
| [`FormulaPart`](./FormulaPart.md) | `src/uqlab/evaluation/signals/formulas.py:16` | 0 | ⚠️ Low |
| [`GaussianLogitsMethod`](./GaussianLogitsMethod.md) | `src/uqlab/evaluation/benchmarks/models/gaussian_logits.py:43` | 1 | ⚠️ Low |
| [`HeteroscedasticMCDropoutResNet`](./HeteroscedasticMCDropoutResNet.md) | `src/uqlab/models/backbones/heteroscedastic_mc_dropout.py:26` | 0 | ⚠️ Low |
| [`InferenceRequest`](./InferenceRequest.md) | `src/uqlab/api/models.py:97` | 0 | ⚠️ Low |
| [`InferenceResponse`](./InferenceResponse.md) | `src/uqlab/api/models.py:125` | 0 | ⚠️ Low |
| [`IntegrityScoreCalculator`](./IntegrityScoreCalculator.md) | `src/uqlab/evaluation/legacy/metrics/integrity_score.py:23` | 1 | ⚠️ Low |
| [`KerasUQMethod`](./KerasUQMethod.md) | `src/uqlab/evaluation/benchmarks/models/base.py:120` | 2 | ⚠️ Low |
| [`LinearHead`](./LinearHead.md) | `src/uqlab/models/architectures.py:29` | 0 | ⚠️ Low |
| [`LoggingCallback`](./LoggingCallback.md) | `src/uqlab/training/callbacks.py:181` | 0 | ⚠️ Low |
| [`MaxVarianceAcquisition`](./MaxVarianceAcquisition.md) | `src/uqlab/evaluation/legacy/metrics/acquisition_functions.py:40` | 0 | ⚠️ Low |
| [`MCDropoutCNN`](./MCDropoutCNN.md) | `src/uqlab/models/backbones/mc_dropout_model.py:86` | 0 | ⚠️ Low |
| [`MCDropoutModel`](./MCDropoutModel.md) | `src/uqlab/models/architectures.py:301` | 0 | ⚠️ Low |
| [`MCDropoutResNet`](./MCDropoutResNet.md) | `src/uqlab/models/backbones/mc_dropout_model.py:12` | 0 | ⚠️ Low |
| [`MetricsCalculator`](./MetricsCalculator.md) | `src/uqlab/evaluation/metrics.py:31` | 0 | ⚠️ Low |
| [`MetricSpec`](./MetricSpec.md) | `src/uqlab/shared/notebook_utils/metrics.py:21` | 0 | ⚠️ Low |
| [`MetricType`](./MetricType.md) | `src/uqlab/shared/types.py:112` | 0 | ⚠️ Low |
| [`MixUp`](./MixUp.md) | `src/uqlab/data/preprocessing.py:248` | 0 | ⚠️ Low |
| [`MLPHead`](./MLPHead.md) | `src/uqlab/models/architectures.py:54` | 0 | ⚠️ Low |
| [`MNISTDataset`](./MNISTDataset.md) | `src/uqlab/data/loaders/mnist_loader.py:15` | 1 | ⚠️ Low |
| [`ModelArchitecture`](./ModelArchitecture.md) | `src/uqlab/shared/types.py:69` | 1 | ⚠️ Low |
| [`ModelCache`](./ModelCache.md) | `src/uqlab/api/models.py:31` | 0 | ⚠️ Low |
| [`ModelInfo`](./ModelInfo.md) | `src/uqlab/api/models.py:83` | 0 | ⚠️ Low |
| [`ModelListResponse`](./ModelListResponse.md) | `src/uqlab/api/models.py:133` | 0 | ⚠️ Low |
| [`ModelLoadRequest`](./ModelLoadRequest.md) | `src/uqlab/api/models.py:74` | 0 | ⚠️ Low |
| [`ModelProtocol`](./ModelProtocol.md) | `src/uqlab/shared/types.py:145` | 0 | ⚠️ Low |
| [`ModelRegistry`](./ModelRegistry.md) | `src/uqlab/models/architectures.py:369` | 0 | ⚠️ Low |
| [`NoiseType`](./NoiseType.md) | `src/uqlab/shared/types.py:49` | 1 | ⚠️ Low |
| [`PredictionResult`](./PredictionResult.md) | `src/uqlab/shared/types.py:217` | 0 | ⚠️ Low |
| [`ProgressCallback`](./ProgressCallback.md) | `src/uqlab/training/callbacks.py:309` | 0 | ⚠️ Low |
| [`PyTorchUQMethod`](./PyTorchUQMethod.md) | `src/uqlab/evaluation/benchmarks/models/base.py:139` | 1 | ⚠️ Low |
| [`RandomAcquisition`](./RandomAcquisition.md) | `src/uqlab/evaluation/legacy/metrics/acquisition_functions.py:151` | 0 | ⚠️ Low |
| [`ResNet18MCDropout`](./ResNet18MCDropout.md) | `src/uqlab/models/factory.py:131` | 1 | ⚠️ Low |
| [`ResNetFeatureExtractor`](./ResNetFeatureExtractor.md) | `src/uqlab/models/feature_extractors.py:280` | 0 | ⚠️ Low |
| [`ResourceManager`](./ResourceManager.md) | `src/uqlab/orchestration/experiment_runner.py:62` | 0 | ⚠️ Low |
| [`ResourceRequirements`](./ResourceRequirements.md) | `src/uqlab/orchestration/experiment_runner.py:37` | 0 | ⚠️ Low |
| [`ResultCollector`](./ResultCollector.md) | `src/uqlab_orchestrator/results/collector.py:13` | 1 | ⚠️ Low |
| [`ResultStorage`](./ResultStorage.md) | `src/uqlab/orchestration/storage.py:25` | 0 | ⚠️ Low |
| [`ResultValidator`](./ResultValidator.md) | `src/uqlab/evaluation/validators.py:193` | 0 | ⚠️ Low |
| [`RiskCoverageArtifacts`](./RiskCoverageArtifacts.md) | `src/uqlab/evaluation/legacy/experiments/risk_coverage_report.py:28` | 0 | ⚠️ Low |
| [`RunArtifacts`](./RunArtifacts.md) | `src/uqlab/run_artifacts.py:40` | 0 | ⚠️ Low |
| [`RunSpecError`](./RunSpecError.md) | `src/uqlab_orchestrator/run_spec.py:27` | 0 | ⚠️ Low |
| [`SignalCalculator`](./SignalCalculator.md) | `src/uqlab/evaluation/signals.py:24` | 0 | ⚠️ Low |
| [`SignalFormulaSpec`](./SignalFormulaSpec.md) | `src/uqlab/evaluation/signals/formulas.py:34` | 0 | ⚠️ Low |
| [`SignalType`](./SignalType.md) | `src/uqlab/shared/types.py:92` | 0 | ⚠️ Low |
| [`SplitSpec`](./SplitSpec.md) | `src/uqlab_classification_backup/data_loader.py:26` | 2 | ⚠️ Low |
| [`SplitType`](./SplitType.md) | `src/uqlab/shared/types.py:59` | 0 | ⚠️ Low |
| [`StandardUQMetrics`](./StandardUQMetrics.md) | `src/uqlab/evaluation/legacy/metrics/standard_uq_metrics.py:22` | 1 | ⚠️ Low |
| [`SurgicalScoreAcquisition`](./SurgicalScoreAcquisition.md) | `src/uqlab/evaluation/legacy/metrics/acquisition_functions.py:91` | 0 | ⚠️ Low |
| [`SurgicalScoreCalculator`](./SurgicalScoreCalculator.md) | `src/uqlab/evaluation/legacy/metrics/surgical_score.py:26` | 1 | ⚠️ Low |
| [`SVHNDataset`](./SVHNDataset.md) | `src/uqlab/data/loaders/svhn_loader.py:12` | 0 | ⚠️ Low |
| [`SweepLoadResult`](./SweepLoadResult.md) | `src/uqlab/shared/notebook_utils/data_utils.py:18` | 0 | ⚠️ Low |
| [`SweepType`](./SweepType.md) | `src/uqlab/shared/types.py:133` | 4 | ✅ High |
| [`TestResNetTrainingModes`](./TestResNetTrainingModes.md) | `src/uqlab/tests/test_resnet_training_modes.py:26` | 0 | ⚠️ Low |
| [`Timer`](./Timer.md) | `src/uqlab/shared/utils/core.py:216` | 1 | ⚠️ Low |
| [`TrainingMode`](./TrainingMode.md) | `src/uqlab/shared/types.py:78` | 1 | ⚠️ Low |
| [`UncertaintyMethod`](./UncertaintyMethod.md) | `src/uqlab/shared/types.py:84` | 1 | ⚠️ Low |
| [`UncertaintyResults`](./UncertaintyResults.md) | `src/uqlab/evaluation/benchmarks/datatypes.py:49` | 1 | ⚠️ Low |
| [`UncertaintySuite`](./UncertaintySuite.md) | `src/uqlab/evaluation/legacy/metrics/uncertainty_suite.py:27` | 0 | ⚠️ Low |
| [`UncertaintyTrainer`](./UncertaintyTrainer.md) | `src/uqlab/training/trainer.py:36` | 1 | ⚠️ Low |
| [`UnifiedRow`](./UnifiedRow.md) | `src/uqlab/results_io.py:84` | 0 | ⚠️ Low |
| [`UQMethod`](./UQMethod.md) | `src/uqlab/evaluation/benchmarks/models/base.py:13` | 2 | ⚠️ Low |
| [`UqModel`](./UqModel.md) | `src/uqlab/evaluation/benchmarks/datatypes.py:31` | 0 | ⚠️ Low |
| [`ValidationResult`](./ValidationResult.md) | `src/uqlab/ui_components/visualization/analysis/correlation_analysis.py:47` | 1 | ⚠️ Low |

## Reuse Opportunities

### High Priority (Well-Reused)
- ✅ **CIFAR10NDataset**: 6 files - Good reuse pattern
- ✅ **Dataset**: 16 files - Good reuse pattern
- ✅ **DualXDATracer**: 3 files - Good reuse pattern
- ✅ **EmbeddingDropoutMLP**: 4 files - Good reuse pattern
- ✅ **ExperimentConfig**: 7 files - Good reuse pattern
- ✅ **ModelConfig**: 3 files - Good reuse pattern
- ✅ **SweepType**: 4 files - Good reuse pattern
- ✅ **TrainingConfig**: 3 files - Good reuse pattern

### Medium Priority (Limited Reuse)
- ⚠️ **AxiomThresholds**: 2 files - Consider consolidation
- ⚠️ **BatchGenerator**: 2 files - Consider consolidation
- ⚠️ **BatchOrchestrator**: 1 files - Consider consolidation
- ⚠️ **Callback**: 1 files - Consider consolidation
- ⚠️ **CallbackList**: 1 files - Consider consolidation
- ⚠️ **CIFAR10NLabelView**: 1 files - Consider consolidation
- ⚠️ **ClassificationDatasetProtocol**: 1 files - Consider consolidation
- ⚠️ **CorrelationResult**: 1 files - Consider consolidation
- ⚠️ **DINOv2Backbone**: 2 files - Consider consolidation
- ⚠️ **EmbeddingDataset**: 1 files - Consider consolidation
- ⚠️ **EmbeddingOrganizer**: 2 files - Consider consolidation
- ⚠️ **ExperimentRunner**: 2 files - Consider consolidation
- ⚠️ **ExperimentTracker**: 1 files - Consider consolidation
- ⚠️ **GaussianLogitsMethod**: 1 files - Consider consolidation
- ⚠️ **IntegrityScoreCalculator**: 1 files - Consider consolidation
- ⚠️ **KerasUQMethod**: 2 files - Consider consolidation
- ⚠️ **MNISTDataset**: 1 files - Consider consolidation
- ⚠️ **ModelArchitecture**: 1 files - Consider consolidation
- ⚠️ **NoiseType**: 1 files - Consider consolidation
- ⚠️ **PyTorchUQMethod**: 1 files - Consider consolidation
- ⚠️ **ResNet18MCDropout**: 1 files - Consider consolidation
- ⚠️ **ResultCollector**: 1 files - Consider consolidation
- ⚠️ **SplitSpec**: 2 files - Consider consolidation
- ⚠️ **StandardUQMetrics**: 1 files - Consider consolidation
- ⚠️ **SurgicalScoreCalculator**: 1 files - Consider consolidation
- ⚠️ **Timer**: 1 files - Consider consolidation
- ⚠️ **TrainingMode**: 1 files - Consider consolidation
- ⚠️ **UncertaintyMethod**: 1 files - Consider consolidation
- ⚠️ **UncertaintyResults**: 1 files - Consider consolidation
- ⚠️ **UncertaintyTrainer**: 1 files - Consider consolidation
- ⚠️ **UQMethod**: 2 files - Consider consolidation
- ⚠️ **ValidationConfig**: 1 files - Consider consolidation
- ⚠️ **ValidationResult**: 1 files - Consider consolidation

### Low Priority (Not Reused)
- ℹ️ **AcquisitionFunction**: No imports - May be internal or unused
- ℹ️ **AleatoricConfig**: No imports - May be internal or unused
- ℹ️ **AsyncBatchRunner**: No imports - May be internal or unused
- ℹ️ **BALDAcquisition**: No imports - May be internal or unused
- ℹ️ **BaselineResNet18**: No imports - May be internal or unused
- ℹ️ **BaselineResNet50**: No imports - May be internal or unused
- ℹ️ **BaselineVGG16**: No imports - May be internal or unused
- ℹ️ **BatchContext**: No imports - May be internal or unused
- ℹ️ **BatchCreate**: No imports - May be internal or unused
- ℹ️ **BatchExperimentConfig**: No imports - May be internal or unused
- ℹ️ **BatchExperimentSummary**: No imports - May be internal or unused
- ℹ️ **BatchListResponse**: No imports - May be internal or unused
- ℹ️ **BatchResponse**: No imports - May be internal or unused
- ℹ️ **BatchRunner**: No imports - May be internal or unused
- ℹ️ **BatchStatus**: No imports - May be internal or unused
- ℹ️ **BatchUpdateRequest**: No imports - May be internal or unused
- ℹ️ **CallbackProtocol**: No imports - May be internal or unused
- ℹ️ **CheckpointCallback**: No imports - May be internal or unused
- ℹ️ **CheckpointConfig**: No imports - May be internal or unused
- ℹ️ **CheckpointManager**: No imports - May be internal or unused
- ℹ️ **CIFAR10Dataset**: No imports - May be internal or unused
- ℹ️ **CIFAR10NLoader**: No imports - May be internal or unused
- ℹ️ **ClassificationModel**: No imports - May be internal or unused
- ℹ️ **CNNFeatureExtractor**: No imports - May be internal or unused
- ℹ️ **CNNMCDropout**: No imports - May be internal or unused
- ℹ️ **ConfigValidator**: No imports - May be internal or unused
- ℹ️ **CutMix**: No imports - May be internal or unused
- ℹ️ **DataConfig**: No imports - May be internal or unused
- ℹ️ **DataLoaderProtocol**: No imports - May be internal or unused
- ℹ️ **DataQualityChecker**: No imports - May be internal or unused
- ℹ️ **DatasetSpec**: No imports - May be internal or unused
- ℹ️ **DeepEnsemble**: No imports - May be internal or unused
- ℹ️ **DINOv2FeatureExtractor**: No imports - May be internal or unused
- ℹ️ **DINOv2WithMCDropout**: No imports - May be internal or unused
- ℹ️ **DropoutHead**: No imports - May be internal or unused
- ℹ️ **DualXDASignalAcquisition**: No imports - May be internal or unused
- ℹ️ **EarlyStoppingCallback**: No imports - May be internal or unused
- ℹ️ **EarlyStoppingConfig**: No imports - May be internal or unused
- ℹ️ **EntropyAcquisition**: No imports - May be internal or unused
- ℹ️ **EpistemicConfig**: No imports - May be internal or unused
- ℹ️ **EvaluationConfig**: No imports - May be internal or unused
- ℹ️ **EvaluationGroup**: No imports - May be internal or unused
- ℹ️ **ExperimentContext**: No imports - May be internal or unused
- ℹ️ **ExperimentCreate**: No imports - May be internal or unused
- ℹ️ **ExperimentResponse**: No imports - May be internal or unused
- ℹ️ **ExperimentStatus**: No imports - May be internal or unused
- ℹ️ **ExperimentVizAnalysis**: No imports - May be internal or unused
- ℹ️ **FeatureExtractor**: No imports - May be internal or unused
- ℹ️ **FormulaOperator**: No imports - May be internal or unused
- ℹ️ **FormulaPart**: No imports - May be internal or unused
- ℹ️ **GlobalConfig**: No imports - May be internal or unused
- ℹ️ **HeteroscedasticMCDropoutResNet**: No imports - May be internal or unused
- ℹ️ **InferenceRequest**: No imports - May be internal or unused
- ℹ️ **InferenceResponse**: No imports - May be internal or unused
- ℹ️ **LinearHead**: No imports - May be internal or unused
- ℹ️ **LoggingCallback**: No imports - May be internal or unused
- ℹ️ **MaxVarianceAcquisition**: No imports - May be internal or unused
- ℹ️ **MCDropoutCNN**: No imports - May be internal or unused
- ℹ️ **MCDropoutModel**: No imports - May be internal or unused
- ℹ️ **MCDropoutResNet**: No imports - May be internal or unused
- ℹ️ **MetricsCalculator**: No imports - May be internal or unused
- ℹ️ **MetricSpec**: No imports - May be internal or unused
- ℹ️ **MetricType**: No imports - May be internal or unused
- ℹ️ **MixUp**: No imports - May be internal or unused
- ℹ️ **MLPHead**: No imports - May be internal or unused
- ℹ️ **ModelCache**: No imports - May be internal or unused
- ℹ️ **ModelInfo**: No imports - May be internal or unused
- ℹ️ **ModelListResponse**: No imports - May be internal or unused
- ℹ️ **ModelLoadRequest**: No imports - May be internal or unused
- ℹ️ **ModelProtocol**: No imports - May be internal or unused
- ℹ️ **ModelRegistry**: No imports - May be internal or unused
- ℹ️ **OptimizerConfig**: No imports - May be internal or unused
- ℹ️ **PathConfig**: No imports - May be internal or unused
- ℹ️ **PathsConfig**: No imports - May be internal or unused
- ℹ️ **PredictionResult**: No imports - May be internal or unused
- ℹ️ **ProgressCallback**: No imports - May be internal or unused
- ℹ️ **RandomAcquisition**: No imports - May be internal or unused
- ℹ️ **RegularizationConfig**: No imports - May be internal or unused
- ℹ️ **ResNetFeatureExtractor**: No imports - May be internal or unused
- ℹ️ **ResourceManager**: No imports - May be internal or unused
- ℹ️ **ResourceRequirements**: No imports - May be internal or unused
- ℹ️ **ResultStorage**: No imports - May be internal or unused
- ℹ️ **ResultValidator**: No imports - May be internal or unused
- ℹ️ **RiskCoverageArtifacts**: No imports - May be internal or unused
- ℹ️ **RunArtifacts**: No imports - May be internal or unused
- ℹ️ **RunSpecError**: No imports - May be internal or unused
- ℹ️ **SchedulerConfig**: No imports - May be internal or unused
- ℹ️ **SignalCalculator**: No imports - May be internal or unused
- ℹ️ **SignalFormulaSpec**: No imports - May be internal or unused
- ℹ️ **SignalType**: No imports - May be internal or unused
- ℹ️ **SplitType**: No imports - May be internal or unused
- ℹ️ **SurgicalScoreAcquisition**: No imports - May be internal or unused
- ℹ️ **SVHNDataset**: No imports - May be internal or unused
- ℹ️ **SweepConfig**: No imports - May be internal or unused
- ℹ️ **SweepLoadResult**: No imports - May be internal or unused
- ℹ️ **SystemConfig**: No imports - May be internal or unused
- ℹ️ **TestResNetTrainingModes**: No imports - May be internal or unused
- ℹ️ **UncertaintySuite**: No imports - May be internal or unused
- ℹ️ **UnifiedBuilderConfig**: No imports - May be internal or unused
- ℹ️ **UnifiedRow**: No imports - May be internal or unused
- ℹ️ **UqModel**: No imports - May be internal or unused
- ℹ️ **WorkflowConfig**: No imports - May be internal or unused
- ℹ️ **WorkflowDatasetConfig**: No imports - May be internal or unused
- ℹ️ **WorkflowEvaluationConfig**: No imports - May be internal or unused
- ℹ️ **WorkflowTrainingConfig**: No imports - May be internal or unused
- ℹ️ **WorkflowUncertaintyConfig**: No imports - May be internal or unused

---
*Generated by Component Reuse Checker*  
*Skill: `.bob/skills/component-reuse-checker.md`*
