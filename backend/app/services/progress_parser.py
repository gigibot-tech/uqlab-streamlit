"""Parse progress from ML script output."""
import re
from typing import Optional

from app.domain.value_objects import ProgressUpdate, TrainingStage


class ProgressParser:
    """Parse training progress from stdout."""

    EPOCH_PATTERN = re.compile(r"Epoch (\d+)/(\d+)")
    STAGE_PATTERNS = {
        "loading": TrainingStage.LOADING_DATA,
        "feature": TrainingStage.EXTRACTING_FEATURES,
        "training": TrainingStage.TRAINING_MODEL,
        "uncertainty": TrainingStage.COMPUTING_UNCERTAINTY,
        "attribution": TrainingStage.COMPUTING_ATTRIBUTION,
        "evaluating": TrainingStage.EVALUATING,
    }

    def parse_line(self, line: str) -> Optional[ProgressUpdate]:
        """Parse a single output line for progress info."""
        line_lower = line.lower()
        
        # Check for epoch progress
        epoch_match = self.EPOCH_PATTERN.search(line)
        if epoch_match:
            current, total = int(epoch_match.group(1)), int(epoch_match.group(2))
            progress = current / total
            return ProgressUpdate(
                progress=progress,
                stage=TrainingStage.TRAINING_MODEL,
                message=f"Epoch {current}/{total}",
                epoch=current,
                total_epochs=total,
            )
        
        # Check for stage keywords
        for keyword, stage in self.STAGE_PATTERNS.items():
            if keyword in line_lower:
                return ProgressUpdate(progress=0.5, stage=stage, message=line[:100])
        
        return None
