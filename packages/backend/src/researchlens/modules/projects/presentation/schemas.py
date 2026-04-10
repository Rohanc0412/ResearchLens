from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CreateProjectRequest(BaseModel):
    name: str
    description: str | None = None

    model_config = ConfigDict(extra="forbid")


class RenameProjectRequest(BaseModel):
    name: str

    model_config = ConfigDict(extra="forbid")


class UpdateProjectRequest(BaseModel):
    name: str | None = None
    description: str | None = None

    model_config = ConfigDict(extra="forbid")


class ProjectResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    description: str | None
    created_by: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(extra="forbid", from_attributes=True)
