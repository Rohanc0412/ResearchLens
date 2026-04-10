from datetime import UTC, datetime
from uuid import uuid4

import pytest

from researchlens.modules.projects.domain import Project
from researchlens.shared.errors import ValidationError


def test_project_create_trims_name() -> None:
    project = Project.create(
        id=uuid4(),
        tenant_id=uuid4(),
        name="  Example  ",
        description="demo",
        created_by="user-1",
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
    )

    assert project.name == "Example"


@pytest.mark.parametrize("value", ["", "   "])
def test_project_create_rejects_blank_name(value: str) -> None:
    with pytest.raises(ValidationError):
        Project.create(
            id=uuid4(),
            tenant_id=uuid4(),
            name=value,
            description=None,
            created_by="user-1",
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )


def test_project_create_rejects_long_name() -> None:
    with pytest.raises(ValidationError):
        Project.create(
            id=uuid4(),
            tenant_id=uuid4(),
            name="x" * 201,
            description=None,
            created_by="user-1",
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
