"""Object-storage abstraction.

Phase 1 default = local filesystem under ``MEDIA_ROOT``. The same interface can
later be backed by S3/GCS without touching callers (see ``get_storage_provider``).
Files are addressed by an opaque ``key``; ``save`` returns a retrievable URL path
of the form ``/media/<key>``.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings
from app.core.logging import logger


@dataclass
class StoredFile:
    key: str
    url: str


class StorageProvider(ABC):
    name: str

    @abstractmethod
    def save(self, key: str, data: bytes) -> StoredFile: ...

    @abstractmethod
    def read(self, key: str) -> bytes: ...

    @abstractmethod
    def delete(self, key: str) -> None: ...

    @abstractmethod
    def url_for(self, key: str) -> str: ...


class LocalStorageProvider(StorageProvider):
    """Stores files on the local filesystem rooted at ``media_root``."""

    name = "local"

    def __init__(self, media_root: str | Path):
        self.media_root = Path(media_root)

    def _path(self, key: str) -> Path:
        # Resolve and ensure the key cannot escape the media root.
        root = self.media_root.resolve()
        dest = (self.media_root / key).resolve()
        if root not in dest.parents and dest != root:
            raise ValueError("Invalid storage key (path traversal detected)")
        return dest

    def url_for(self, key: str) -> str:
        return f"/media/{key}"

    def save(self, key: str, data: bytes) -> StoredFile:
        dest = self._path(key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        logger.info("[STORAGE:local] saved %d bytes -> %s", len(data), key)
        return StoredFile(key=key, url=self.url_for(key))

    def read(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def delete(self, key: str) -> None:
        path = self._path(key)
        if path.exists():
            path.unlink()


def get_storage_provider() -> StorageProvider:
    # Future: if settings.s3_bucket: return S3StorageProvider(...)
    return LocalStorageProvider(settings.media_root)
