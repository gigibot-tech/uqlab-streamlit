"""Value objects for the training domain."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TrainingStage(str, Enum):
    """Training pipeline stages."""

    INITIALIZING = "initializing"
    LOADING_DATA = "loading_data"
    EXTRACTING_FEATURES = "extracting_features"
    TRAINING_MODEL = "training_model"
    COMPUTING_UNCERTAINTY = "computing_uncertainty"
    COMPUTING_ATTRIBUTION = "computing_attribution"
    EVALUATING = "evaluating"
    SAVING_RESULTS = "saving_results"
    COMPLETED = "completed"
    FAILED = "failed"


class ProgressUpdate(BaseModel):
    """Progress update from training process."""

    progress: float = Field(ge=0.0, le=1.0, description="Progress percentage (0.0 to 1.0)")
    stage: TrainingStage = Field(description="Current training stage")
    message: str = Field(description="Human-readable status message")
    epoch: Optional[int] = Field(None, description="Current epoch number")
    total_epochs: Optional[int] = Field(None, description="Total number of epochs")

    class Config:
        """Pydantic config."""

        frozen = True  # Immutable value object


class TrainingMetrics(BaseModel):
    """Training metrics collected during the process."""

    train_loss: Optional[float] = None
    train_accuracy: Optional[float] = None
    val_loss: Optional[float] = None
    val_accuracy: Optional[float] = None

    class Config:
        """Pydantic config."""

        frozen = True


# Made with Bob