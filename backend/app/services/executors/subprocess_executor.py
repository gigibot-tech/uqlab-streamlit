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
        """Execute training script and return results."""
        cmd = [self.python_exe, str(self.script_path), "--config", str(config_path), "--output_dir", str(output_dir)]
        
        progress_callback(ProgressUpdate(progress=0.0, stage=TrainingStage.INITIALIZING, message="Starting..."))
        
        process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        _, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise RuntimeError(f"Training failed: {stderr.decode()}")
        
        progress_callback(ProgressUpdate(progress=1.0, stage=TrainingStage.COMPLETED, message="Completed"))
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
