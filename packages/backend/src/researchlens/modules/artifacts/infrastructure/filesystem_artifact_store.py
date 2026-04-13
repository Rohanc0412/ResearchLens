import hashlib
from pathlib import Path

from researchlens.modules.artifacts.application.ports import ArtifactStorage, StoredArtifactBytes
from researchlens.shared.errors import InfrastructureError, ValidationError


class FilesystemArtifactStore(ArtifactStorage):
    def __init__(self, *, root: Path) -> None:
        self._root = root.resolve()

    async def write(self, *, storage_key: str, content: bytes) -> StoredArtifactBytes:
        path = self._resolve(storage_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return StoredArtifactBytes(
            backend="local",
            storage_key=storage_key,
            byte_size=len(content),
            sha256=hashlib.sha256(content).hexdigest(),
        )

    async def read(self, *, storage_key: str) -> bytes:
        path = self._resolve(storage_key)
        if not path.exists():
            raise InfrastructureError("Stored artifact bytes are missing.")
        return path.read_bytes()

    def _resolve(self, storage_key: str) -> Path:
        key_path = Path(storage_key)
        if key_path.is_absolute() or ".." in key_path.parts:
            raise ValidationError("Artifact storage key is invalid.")
        resolved = (self._root / key_path).resolve()
        if self._root not in resolved.parents and resolved != self._root:
            raise ValidationError("Artifact storage key escapes artifact root.")
        return resolved
