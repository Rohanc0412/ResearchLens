from pathlib import Path
from uuid import uuid4

from alembic import command
from alembic.config import Config
from pytest import MonkeyPatch


def test_alembic_upgrade_head_smoke(monkeypatch: MonkeyPatch) -> None:
    database_dir = Path(".data/test-dbs")
    database_dir.mkdir(parents=True, exist_ok=True)
    database_path = database_dir / f"alembic-smoke-{uuid4()}.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{database_path.as_posix()}")
    config = Config("packages/backend/alembic.ini")

    command.upgrade(config, "head")

    assert Path(database_path).exists()
