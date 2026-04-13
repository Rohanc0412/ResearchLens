from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ArtifactResponse(BaseModel):
    id: UUID
    run_id: UUID
    kind: str
    filename: str
    media_type: str
    storage_backend: str
    byte_size: int
    sha256: str
    created_at: datetime
    manifest_id: UUID | None

    model_config = ConfigDict(extra="forbid", from_attributes=True)
