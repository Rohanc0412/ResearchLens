from pathlib import Path


def test_python_code_contains_no_sys_path_insert() -> None:
    for file_path in Path("apps").rglob("*.py"):
        assert "sys.path.insert" not in file_path.read_text(encoding="utf-8")

    for file_path in Path("packages/backend/src").rglob("*.py"):
        assert "sys.path.insert" not in file_path.read_text(encoding="utf-8")


def test_runtime_configs_contain_no_pythonpath_hacks() -> None:
    files = [
        Path("Makefile"),
        Path("justfile"),
        Path(".github/workflows/ci.yml"),
        Path("infra/docker/api.Dockerfile"),
        Path("infra/docker/worker.Dockerfile"),
        Path("infra/compose/docker-compose.dev.yml"),
        Path("packages/backend/alembic.ini"),
    ]

    for file_path in files:
        contents = file_path.read_text(encoding="utf-8")
        assert "PYTHONPATH" not in contents
        assert "prepend_sys_path" not in contents
