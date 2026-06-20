from __future__ import annotations

import logging

from app.core.config import settings
from app.storage.base import StorageBackend
from app.storage.filesystem import FilesystemStorageBackend
from app.storage.s3 import S3StorageBackend

logger = logging.getLogger(__name__)

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

# Made with Bob
