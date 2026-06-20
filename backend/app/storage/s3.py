from __future__ import annotations

import logging
from pathlib import Path

from app.core.config import settings
from app.storage.base import StorageBackend

logger = logging.getLogger(__name__)


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
            logger.warning("S3 storage requested but optional dependencies are unavailable: %s", self._import_error)
            return False
        return True

# Made with Bob
