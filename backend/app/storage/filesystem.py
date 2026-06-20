from __future__ import annotations

from pathlib import Path

from app.storage.base import StorageBackend


class FilesystemStorageBackend(StorageBackend):
    @property
    def name(self) -> str:
        return "filesystem"

    def prepare_directory(self, path: Path) -> Path:
        path.mkdir(parents=True, exist_ok=True)
        return path

    def is_available(self) -> bool:
        return True

# Made with Bob
