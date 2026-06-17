"""Direct import executor - runs ML code in-process with asyncio.to_thread."""
import asyncio
import json
import logging
import sys
import threading
from pathlib import Path
from typing import Callable, Optional

from app.core.ml_bootstrap import ensure_ml_paths
from app.domain.models import TrainingResult
from app.domain.value_objects import ProgressUpdate, TrainingStage
from app.services.executors.base import TrainingExecutor

logger = logging.getLogger(__name__)

# Only one in-process training run at a time (shared sys.argv / reloaded module).
_TRAINING_LOCK = threading.Lock()

# Global progress callback that ML scripts can use
_GLOBAL_PROGRESS_CALLBACK: Optional[Callable[[ProgressUpdate], None]] = None

def set_progress_callback(callback: Optional[Callable[[ProgressUpdate], None]]) -> None:
    """Set the global progress callback for ML scripts to use."""
    global _GLOBAL_PROGRESS_CALLBACK
    _GLOBAL_PROGRESS_CALLBACK = callback

def get_progress_callback() -> Optional[Callable[[ProgressUpdate], None]]:
    """Get the current global progress callback."""
    return _GLOBAL_PROGRESS_CALLBACK


class DirectExecutor(TrainingExecutor):
    """
    Execute ML training by directly importing and calling the script.
    
    Configuration:
    - USE_THREAD_POOL: Set to False to run in main thread (blocks event loop but simpler)
    - USE_THREAD_POOL: Set to True to run in thread pool (non-blocking, recommended)
    """
    
    USE_THREAD_POOL = True  # Set to False to run in main thread (simpler but blocking)

    def __init__(self, script_path: Path):
        self.script_path = script_path
        # ``uqlab`` comes from editable install (``uv sync`` in backend/).
        # Repo root: ``uq_classification`` symlink; scripts/: training module name.
        scripts_dir = script_path.parent
        project_root = ensure_ml_paths(scripts_dir=scripts_dir)

        logger.info(
            "Python path for training: scripts=%s, project_root=%s",
            scripts_dir,
            project_root,
        )
        
        # Validate script exists
        if not script_path.exists():
            raise FileNotFoundError(f"ML script not found: {script_path}")
        logger.info(f"✅ ML script found at: {script_path}")
        
        # Pre-flight check: verify imports work
        self._verify_imports()
    
    def _verify_imports(self):
        """Verify that all required modules can be imported."""
        try:
            # Test critical imports (using new paths after refactoring)
            from uqlab.evaluation.classification.models import EmbeddingDataset
            from uqlab.evaluation.classification.config import ExperimentConfig
            from uqlab.data.loaders.cifar10n_loader import CIFAR10NDataset
            assert EmbeddingDataset is not None and ExperimentConfig is not None
            logger.info("✅ Pre-flight check passed: All required modules can be imported")
        except ImportError as e:
            logger.error(f"❌ Pre-flight check failed: {e}", exc_info=True)
            raise RuntimeError(f"Missing required dependencies: {e}") from e

    async def execute(
        self, config_path: Path, output_dir: Path, progress_callback: Callable[[ProgressUpdate], None]
    ) -> TrainingResult:
        """Execute training by directly importing the main function."""
        logger.info("=" * 80)
        logger.info(f"DIRECT IMPORT EXECUTION")
        logger.info(f"Script: {self.script_path}")
        logger.info(f"Config: {config_path} (exists: {config_path.exists()})")
        logger.info(f"Output: {output_dir} (exists: {output_dir.exists()})")
        logger.info("=" * 80)

        progress_callback(ProgressUpdate(
            progress=0.0,
            stage=TrainingStage.INITIALIZING,
            message="Importing ML script...",
            epoch=None,
            total_epochs=None
        ))

        try:
            if self.USE_THREAD_POOL:
                # Run in thread pool to not block event loop (recommended)
                logger.info("Running training in thread pool (non-blocking)")
                result = await asyncio.to_thread(
                    self._run_training_sync,
                    config_path,
                    output_dir,
                    progress_callback
                )
            else:
                # Run in main thread (simpler but blocks event loop)
                logger.warning("Running training in main thread (BLOCKING - not recommended for production)")
                result = self._run_training_sync(config_path, output_dir, progress_callback)
            
            logger.info("Training completed successfully")
            progress_callback(ProgressUpdate(
                progress=1.0,
                stage=TrainingStage.COMPLETED,
                message="Training completed",
                epoch=None,
                total_epochs=None
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
        """Run training under the global lock (no concurrent sys.argv)."""
        # Set up sys.argv to simulate command line args
        original_argv = sys.argv.copy()
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        
        try:
            # Import the main function (do this inside try block to catch import errors)
            import importlib
            import run_fast_uncertainty_classification
            # Force reload to pick up any changes to the script
            importlib.reload(run_fast_uncertainty_classification)
            from run_fast_uncertainty_classification import main
            
            # Set the global progress callback so ML script can use it
            set_progress_callback(progress_callback)
            
            sys.argv = [
                str(self.script_path),
                "--config", str(config_path),
                "--output_dir", str(output_dir)
            ]
            
            logger.info(f"Calling main() with args: {sys.argv}")
            progress_callback(ProgressUpdate(
                progress=0.1,
                stage=TrainingStage.LOADING_DATA,
                message="Initializing training...",
                epoch=None,
                total_epochs=None
            ))
            
            # Call the main function
            logger.info("Starting ML training script execution...")
            main()
            logger.info("ML training script completed successfully")
            
            # Final progress update
            progress_callback(ProgressUpdate(
                progress=0.95,
                stage=TrainingStage.SAVING_RESULTS,
                message="Reading results...",
                epoch=None,
                total_epochs=None
            ))
            
            # Read results
            return self._read_results(output_dir)
            
        except ImportError as e:
            error_msg = f"Failed to import training script: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg) from e
        finally:
            # Always restore original state
            sys.argv = original_argv
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            # Clear the global progress callback
            set_progress_callback(None)

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
        
        # Extract per-signal AUROC data (7 signals × 2 uncertainty types)
        one_vs_rest_auroc = data.get("one_vs_rest_auroc", [])
        
        # Build best_signals dict with complete per-signal AUROC structure
        best_signals = {
            "one_vs_rest_auroc": one_vs_rest_auroc  # Pass through complete 7×2 structure
        }
        
        # Compute aggregated max values for backward compatibility
        aleatoric_auroc = max((s.get("aleatoric_like_auroc", 0.0) for s in one_vs_rest_auroc), default=0.0)
        epistemic_auroc = max((s.get("epistemic_like_auroc", 0.0) for s in one_vs_rest_auroc), default=0.0)
        
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

# Made with Bob
