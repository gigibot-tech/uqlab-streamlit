from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class StorageBackend(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable backend name."""
        raise NotImplementedError

    @abstractmethod
    def prepare_directory(self, path: Path) -> Path:
        """Ensure a directory exists and return its local path."""
        raise NotImplementedError

    @abstractmethod
    def is_available(self) -> bool:
        """Return whether the backend is currently usable."""
        raise NotImplementedError

# Made with Bob
