from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID

from researchlens.shared.errors import ValidationError

MAX_PROJECT_NAME_LENGTH = 200
MAX_CREATED_BY_LENGTH = 200


def normalize_project_name(name: str) -> str:
    normalized_name = name.strip()
    if not normalized_name:
        raise ValidationError("Project name is required.")
    if len(normalized_name) > MAX_PROJECT_NAME_LENGTH:
        raise ValidationError("Project name must be 200 characters or fewer.")
    return normalized_name


def validate_created_by(created_by: str) -> str:
    normalized_created_by = created_by.strip()
    if not normalized_created_by:
        raise ValidationError("Actor user id is required.")
    if len(normalized_created_by) > MAX_CREATED_BY_LENGTH:
        raise ValidationError("Actor user id must be 200 characters or fewer.")
    return normalized_created_by


@dataclass(frozen=True, slots=True)
class Project:
    id: UUID
    tenant_id: UUID
    name: str
    description: str | None
    created_by: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        *,
        id: UUID,
        tenant_id: UUID,
        name: str,
        description: str | None,
        created_by: str,
        created_at: datetime,
        updated_at: datetime,
    ) -> "Project":
        return cls(
            id=id,
            tenant_id=tenant_id,
            name=normalize_project_name(name),
            description=description,
            created_by=validate_created_by(created_by),
            created_at=created_at,
            updated_at=updated_at,
        )

    def rename(self, *, new_name: str, updated_at: datetime) -> "Project":
        return replace(
            self,
            name=normalize_project_name(new_name),
            updated_at=updated_at,
        )
