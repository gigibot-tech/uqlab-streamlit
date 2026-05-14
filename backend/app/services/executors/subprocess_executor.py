"""Subprocess executor for ML training script."""
import asyncio
import json
import logging
from pathlib import Path
from typing import Callable

from app.domain.models import TrainingResult
from app.domain.value_objects import ProgressUpdate, TrainingStage
from app.services.executors.base import TrainingExecutor

logger = logging.getLogger(__name__)


class SubprocessExecutor(TrainingExecutor):
    """Execute ML training script as subprocess."""

    def __init__(self, script_path: Path, python_exe: str = "python"):
        self.script_path = script_path
        self.python_exe = python_exe

    async def execute(
        self, config_path: Path, output_dir: Path, progress_callback: Callable[[ProgressUpdate], None]
    ) -> TrainingResult:
        """Execute training script and stream output in real-time."""
        cmd = [self.python_exe, str(self.script_path), "--config", str(config_path), "--output_dir", str(output_dir)]
        
        logger.info(f"Starting training: {' '.join(cmd)}")
        progress_callback(ProgressUpdate(
            progress=0.0,
            stage=TrainingStage.INITIALIZING,
            message="Starting training...",
            epoch=None,
            total_epochs=None
        ))
        
        # Start process with stdout/stderr pipes
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,  # Merge stderr into stdout
        )
        
        # Stream output line by line
        if process.stdout:
            async for line in process.stdout:
                line_str = line.decode().strip()
                if line_str:
                    logger.info(f"[Training] {line_str}")
                    # Update progress based on output
                    progress_callback(ProgressUpdate(
                        progress=0.5,
                        stage=TrainingStage.TRAINING_MODEL,
                        message=line_str[:100],  # Truncate long lines
                        epoch=None,
                        total_epochs=None
                    ))
        
        # Wait for process to complete
        await process.wait()
        
        if process.returncode != 0:
            error_msg = f"Training failed with exit code {process.returncode}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        logger.info("Training completed successfully")
        progress_callback(ProgressUpdate(
            progress=1.0,
            stage=TrainingStage.COMPLETED,
            message="Training completed",
            epoch=None,
            total_epochs=None
        ))
        return self._read_results(output_dir)

    def _read_results(self, output_dir: Path) -> TrainingResult:
        """Read results from summary.json."""
        with open(output_dir / "summary.json") as f:
            data = json.load(f)
        aurocs = data.get("one_vs_rest_auroc", [])
        return TrainingResult(
            aleatoric_auroc=max((s.get("aleatoric_like_auroc", 0.0) for s in aurocs), default=0.0),
            epistemic_auroc=max((s.get("epistemic_like_auroc", 0.0) for s in aurocs), default=0.0),
            train_size=data.get("train_size", 0),
            eval_sizes=data.get("eval_sizes", {}),
            results_path=str(output_dir),
        )
