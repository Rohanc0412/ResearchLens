import ast
from pathlib import Path

MODULE_NAMES = {
    "auth",
    "projects",
    "conversations",
    "runs",
    "retrieval",
    "drafting",
    "evaluation",
    "repair",
    "evidence",
    "artifacts",
}


def _owner_module_name(path: Path) -> str:
    parts = path.parts
    module_index = parts.index("modules")
    return parts[module_index + 1]


def _iter_import_targets(file_path: Path) -> list[str]:
    tree = ast.parse(file_path.read_text(encoding="utf-8"))
    imports: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)

    return imports


def test_backend_modules_do_not_cross_import_each_other() -> None:
    root = Path("packages/backend/src/researchlens/modules")

    for file_path in root.rglob("*.py"):
        owner = _owner_module_name(file_path)
        for target in _iter_import_targets(file_path):
            for candidate in MODULE_NAMES - {owner}:
                assert not target.startswith(f"researchlens.modules.{candidate}")


def test_app_entrypoints_do_not_import_business_modules() -> None:
    for package_root in [
        Path("apps/api/src/researchlens_api"),
        Path("apps/worker/src/researchlens_worker"),
    ]:
        for file_path in package_root.rglob("*.py"):
            for target in _iter_import_targets(file_path):
                if package_root.name == "researchlens_api":
                    assert ".application" not in target
                    assert ".domain" not in target
                else:
                    assert not target.startswith("researchlens.modules.")


def test_domain_layers_do_not_import_framework_or_infrastructure_modules() -> None:
    for file_path in Path("packages/backend/src/researchlens/modules").rglob("domain/*.py"):
        for target in _iter_import_targets(file_path):
            assert not target.startswith("fastapi")
            assert not target.startswith("sqlalchemy.orm")
            assert not target.startswith("sqlalchemy.ext.asyncio")
            assert ".presentation" not in target
            assert ".infrastructure" not in target


def test_presentation_layers_do_not_reach_into_infrastructure() -> None:
    for file_path in Path("packages/backend/src/researchlens/modules").rglob("presentation/*.py"):
        for target in _iter_import_targets(file_path):
            assert ".infrastructure" not in target
            assert not target.startswith("sqlalchemy")


def test_projects_application_does_not_import_sqlalchemy() -> None:
    root = Path("packages/backend/src/researchlens/modules/projects/application")
    for file_path in root.rglob("*.py"):
        for target in _iter_import_targets(file_path):
            assert not target.startswith("sqlalchemy")
