"""Deprecated subprocess executor — production uses DirectExecutor + pipeline.run."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from app.domain.models import TrainingResult
from app.domain.value_objects import ProgressUpdate
from app.services.executors.base import TrainingExecutor


class SubprocessExecutor(TrainingExecutor):
    """
    .. deprecated::
        Removed. Use :class:`DirectExecutor` which calls ``uqlab.runner.pipeline.run``.
    """

    def __init__(self, script_path: Path, python_exe: str = "python"):
        self.script_path = script_path
        self.python_exe = python_exe

    async def execute(
        self,
        config_path: Path,
        output_dir: Path,
        progress_callback: Callable[[ProgressUpdate], None],
    ) -> TrainingResult:
        raise NotImplementedError(
            "SubprocessExecutor is retired; use DirectExecutor (in-process pipeline.run)."
        )
