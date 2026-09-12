from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)


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


class FilesystemStorageBackend(StorageBackend):
    @property
    def name(self) -> str:
        return "filesystem"

    def prepare_directory(self, path: Path) -> Path:
        path.mkdir(parents=True, exist_ok=True)
        return path

    def is_available(self) -> bool:
        return True


class S3StorageBackend(StorageBackend):
    def __init__(self) -> None:
        self._import_error: Exception | None = None
        self._client_available = False
        try:
            import aioboto3  # noqa: F401
            import aiobotocore  # noqa: F401

            self._client_available = True
        except Exception as exc:
            self._import_error = exc

    @property
    def name(self) -> str:
        return "s3"

    def prepare_directory(self, path: Path) -> Path:
        path.mkdir(parents=True, exist_ok=True)
        return path

    def is_available(self) -> bool:
        required = [
            settings.STORAGE_S3_ENDPOINT_URL,
            settings.STORAGE_S3_BUCKET,
            settings.STORAGE_S3_ACCESS_KEY_ID,
            settings.STORAGE_S3_SECRET_ACCESS_KEY,
        ]
        if not all(required):
            return False
        if not self._client_available:
            logger.warning(
                "S3 storage requested but optional dependencies are unavailable: %s",
                self._import_error,
            )
            return False
        return True


_storage_backend: StorageBackend | None = None


def get_storage_backend() -> StorageBackend:
    global _storage_backend
    if _storage_backend is not None:
        return _storage_backend

    if settings.STORAGE_BACKEND == "s3":
        s3_backend = S3StorageBackend()
        if s3_backend.is_available():
            endpoint = settings.STORAGE_S3_ENDPOINT_URL or "AWS S3"
            if "localhost" in endpoint or "127.0.0.1" in endpoint:
                logger.info(f"Storage backend: s3 (local MinIO at {endpoint})")
            else:
                logger.info(f"Storage backend: s3 (endpoint: {endpoint})")
            _storage_backend = s3_backend
            return _storage_backend
        logger.warning("S3 storage configured but unavailable. Falling back to filesystem.")

    _storage_backend = FilesystemStorageBackend()
    logger.info("Storage backend: filesystem")
    return _storage_backend
