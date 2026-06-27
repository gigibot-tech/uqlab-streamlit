"""Direct import executor - runs ML via ``uqlab.runner.execute.run_from_yaml`` in-process."""
import asyncio
import json
import logging
import threading
from pathlib import Path
from typing import Any, Callable, Optional

from app.core.ml_bootstrap import ensure_ml_paths, reload_training_modules
from app.domain.models import TrainingResult
from app.domain.value_objects import ProgressUpdate, TrainingStage
from app.services.executors.base import TrainingExecutor

logger = logging.getLogger(__name__)

# Only one in-process training run at a time (shared sys.argv / reloaded module).
_TRAINING_LOCK = threading.Lock()

PipelineRunFn = Callable[..., dict[str, Any]]


class DirectExecutor(TrainingExecutor):
    """
    Execute ML training by calling the canonical runner pipeline in-process.

    Configuration:
    - USE_THREAD_POOL: Set to False to run in main thread (blocks event loop but simpler)
    - USE_THREAD_POOL: Set to True to run in thread pool (non-blocking, recommended)
    """

    USE_THREAD_POOL = True

    def __init__(self, pipeline_run: PipelineRunFn | None = None):
        self._pipeline_run = pipeline_run
        project_root = ensure_ml_paths()
        logger.info("Python path for training: project_root=%s", project_root)
        self._verify_imports()

    def _resolve_pipeline_run(self) -> PipelineRunFn:
        if self._pipeline_run is not None:
            return self._pipeline_run
        from uqlab.runner.execute import run_from_yaml as pipeline_run

        return pipeline_run

    def _verify_imports(self) -> None:
        """Verify that the ML stack and runner entry import cleanly."""
        try:
            from uqlab.data.preprocessing import get_dataset_image_transform
            from uqlab.runner.experiment_core import run_experiment_core
            from uqlab.shared.config.classification import ExperimentConfig
            from uqlab.models.classification_models import EmbeddingDataset

            assert get_dataset_image_transform("cifar10") is not None
            assert EmbeddingDataset is not None and ExperimentConfig is not None
            assert callable(run_experiment_core)

            reload_training_modules()
            pipeline_run = self._resolve_pipeline_run()
            assert callable(pipeline_run)

            logger.info(
                "Pre-flight check passed: uqlab.runner.execute.run_from_yaml and experiment_core import cleanly"
            )
        except ImportError as e:
            logger.error("Pre-flight check failed: %s", e, exc_info=True)
            raise RuntimeError(f"Missing required dependencies: {e}") from e

    async def execute(
        self, config_path: Path, output_dir: Path, progress_callback: Callable[[ProgressUpdate], None]
    ) -> TrainingResult:
        """Execute training via the injected or default runner pipeline."""
        logger.info("=" * 80)
        logger.info("DIRECT IMPORT EXECUTION")
        logger.info("Runner: uqlab.runner.execute.run_from_yaml")
        logger.info("Config: %s (exists: %s)", config_path, config_path.exists())
        logger.info("Output: %s (exists: %s)", output_dir, output_dir.exists())
        logger.info("=" * 80)

        progress_callback(ProgressUpdate(
            progress=0.0,
            stage=TrainingStage.INITIALIZING,
            message="Starting runner pipeline...",
            epoch=None,
            total_epochs=None,
        ))

        try:
            if self.USE_THREAD_POOL:
                logger.info("Running training in thread pool (non-blocking)")
                result = await asyncio.to_thread(
                    self._run_training_sync,
                    config_path,
                    output_dir,
                    progress_callback,
                )
            else:
                logger.warning(
                    "Running training in main thread (BLOCKING - not recommended for production)"
                )
                result = self._run_training_sync(config_path, output_dir, progress_callback)

            logger.info("Training completed successfully")
            progress_callback(ProgressUpdate(
                progress=1.0,
                stage=TrainingStage.COMPLETED,
                message="Training completed",
                epoch=None,
                total_epochs=None,
            ))

            return result

        except Exception as e:
            error_msg = f"Training failed: {str(e)}"
            logger.error("=" * 80)
            logger.error(error_msg, exc_info=True)
            logger.error("=" * 80)
            raise RuntimeError(error_msg) from e

    def _run_training_sync(
        self, config_path: Path, output_dir: Path, progress_callback: Callable[[ProgressUpdate], None]
    ) -> TrainingResult:
        """Run training synchronously (called in thread pool)."""
        with _TRAINING_LOCK:
            return self._run_training_sync_locked(config_path, output_dir, progress_callback)

    def _run_training_sync_locked(
        self, config_path: Path, output_dir: Path, progress_callback: Callable[[ProgressUpdate], None]
    ) -> TrainingResult:
        """Run training under the global lock via the canonical runner pipeline."""
        progress_callback(ProgressUpdate(
            progress=0.1,
            stage=TrainingStage.LOADING_DATA,
            message="Loading config and starting pipeline...",
            epoch=None,
            total_epochs=None,
        ))

        pipeline_run = self._resolve_pipeline_run()
        logger.info(
            "Calling uqlab.runner.execute.run_from_yaml(config=%s, output=%s)",
            config_path,
            output_dir,
        )
        pipeline_run(
            config_path,
            output_dir,
            progress_callback=progress_callback,
        )

        progress_callback(ProgressUpdate(
            progress=0.95,
            stage=TrainingStage.SAVING_RESULTS,
            message="Reading results...",
            epoch=None,
            total_epochs=None,
        ))
        return self._read_results(output_dir)

    def _read_results(self, output_dir: Path) -> TrainingResult:
        """Read results from summary.json, or rebuild from results.pt if needed."""
        summary_file = output_dir / "summary.json"
        data: dict

        if summary_file.exists():
            with open(summary_file) as f:
                data = json.load(f)
        else:
            data = self._load_results_fallback(output_dir)
            if data is None:
                raise FileNotFoundError(
                    f"Results file not found: {summary_file} "
                    f"(also no results.pt under {output_dir})"
                )
            logger.warning(
                "summary.json missing in %s — loaded metrics from results.pt",
                output_dir,
            )

        one_vs_rest_auroc = data.get("one_vs_rest_auroc", [])
        best_signals = {
            "one_vs_rest_auroc": one_vs_rest_auroc,
        }

        def _max_auroc(key: str) -> float | None:
            vals = []
            for s in one_vs_rest_auroc:
                v = s.get(key)
                if v is None:
                    continue
                try:
                    fv = float(v)
                    if fv == fv:
                        vals.append(fv)
                except (TypeError, ValueError):
                    continue
            return max(vals) if vals else None

        aleatoric_auroc = _max_auroc("aleatoric_like_auroc")
        epistemic_auroc = _max_auroc("epistemic_like_auroc")

        return TrainingResult(
            aleatoric_auroc=aleatoric_auroc,
            epistemic_auroc=epistemic_auroc,
            train_size=data.get("train_size", 0),
            eval_sizes=data.get("eval_sizes", {}),
            best_signals=best_signals,
            results_path=str(output_dir),
        )

    def _load_results_fallback(self, output_dir: Path) -> dict | None:
        """Build summary-shaped dict from results.pt when summary.json is absent."""
        results_pt = output_dir / "results.pt"
        if not results_pt.exists():
            return None
        try:
            from uqlab.run_artifacts import load_run_directory

            artifacts = load_run_directory(output_dir)
            if artifacts.source == "none":
                return None
            return {
                "train_size": artifacts.train_size or 0,
                "eval_sizes": artifacts.eval_sizes or {},
                "one_vs_rest_auroc": artifacts.one_vs_rest_auroc or [],
            }
        except Exception as exc:
            logger.warning("Could not load fallback results from %s: %s", output_dir, exc)
            return None
