"""Direct import executor - runs ML code in-process with asyncio.to_thread."""
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Callable, Optional

from app.domain.models import TrainingResult
from app.domain.value_objects import ProgressUpdate, TrainingStage
from app.services.executors.base import TrainingExecutor

logger = logging.getLogger(__name__)

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
        # Add both scripts directory AND project root to Python path
        scripts_dir = script_path.parent
        project_root = scripts_dir.parent  # Go up one more level to walaris-cen
        
        for path in [str(scripts_dir), str(project_root)]:
            if path not in sys.path:
                sys.path.insert(0, path)
        
        logger.info(f"Added to sys.path: {scripts_dir}, {project_root}")
        
        # Validate script exists
        if not script_path.exists():
            raise FileNotFoundError(f"ML script not found: {script_path}")
        logger.info(f"✅ ML script found at: {script_path}")
        
        # Pre-flight check: verify imports work
        self._verify_imports()
    
    def _verify_imports(self):
        """Verify that all required modules can be imported."""
        try:
            # Test critical imports
            import uq_classification
            from src.data.cifar10n_loader import CIFAR10NDataset
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
        # Set up sys.argv to simulate command line args
        original_argv = sys.argv.copy()
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        
        try:
            # Import the main function (do this inside try block to catch import errors)
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
        """Read results from summary.json."""
        summary_file = output_dir / "summary.json"
        if not summary_file.exists():
            raise FileNotFoundError(f"Results file not found: {summary_file}")
            
        with open(summary_file) as f:
            data = json.load(f)
        
        aurocs = data.get("one_vs_rest_auroc", [])
        return TrainingResult(
            aleatoric_auroc=max((s.get("aleatoric_like_auroc", 0.0) for s in aurocs), default=0.0),
            epistemic_auroc=max((s.get("epistemic_like_auroc", 0.0) for s in aurocs), default=0.0),
            train_size=data.get("train_size", 0),
            eval_sizes=data.get("eval_sizes", {}),
            results_path=str(output_dir),
        )

# Made with Bob
