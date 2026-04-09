from pathlib import Path

from alembic import command
from alembic.config import Config
from pytest import MonkeyPatch


def test_alembic_upgrade_head_smoke(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    database_path = tmp_path / "alembic-smoke.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{database_path.as_posix()}")
    config = Config("packages/backend/alembic.ini")

    command.upgrade(config, "head")

    assert Path(database_path).exists()
