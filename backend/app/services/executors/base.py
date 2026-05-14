"""Base executor interface using Strategy pattern."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable

from app.domain.models import TrainingResult
from app.domain.value_objects import ProgressUpdate


class TrainingExecutor(ABC):
    """Abstract base class for training executors (Strategy pattern)."""

    @abstractmethod
    async def execute(
        self,
        config_path: Path,
        output_dir: Path,
        progress_callback: Callable[[ProgressUpdate], None],
    ) -> TrainingResult:
        """
        Execute training job and return results.

        Args:
            config_path: Path to YAML configuration file
            output_dir: Directory for output files
            progress_callback: Callback function for progress updates

        Returns:
            TrainingResult with AUROC scores and metadata

        Raises:
            RuntimeError: If training fails
        """
        pass


# Made with Bob