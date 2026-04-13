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
        allow_runs_orchestration = (
            owner == "runs"
            and "orchestration" in file_path.parts
            and file_path.name != "__init__.py"
        )
        for target in _iter_import_targets(file_path):
            for candidate in MODULE_NAMES - {owner}:
                if (
                    allow_runs_orchestration
                    and candidate in {"retrieval", "drafting", "evaluation", "repair"}
                    and target.startswith(f"researchlens.modules.{candidate}.orchestration")
                ):
                    continue
                if (
                    allow_runs_orchestration
                    and candidate == "artifacts"
                    and target.startswith("researchlens.modules.artifacts.orchestration")
                ):
                    continue
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


def test_application_layers_do_not_import_module_infrastructure() -> None:
    root = Path("packages/backend/src/researchlens/modules")
    for file_path in root.rglob("application/*.py"):
        owner = _owner_module_name(file_path)
        forbidden = f"researchlens.modules.{owner}.infrastructure"
        for target in _iter_import_targets(file_path):
            assert not target.startswith(forbidden)


def test_orchestration_layers_do_not_import_module_infrastructure() -> None:
    root = Path("packages/backend/src/researchlens/modules")
    for file_path in root.rglob("orchestration/*.py"):
        owner = _owner_module_name(file_path)
        forbidden = f"researchlens.modules.{owner}.infrastructure"
        for target in _iter_import_targets(file_path):
            assert not target.startswith(forbidden)


def test_python_production_files_stay_under_hard_size_caps() -> None:
    root = Path("packages/backend/src")
    for file_path in root.rglob("*.py"):
        line_count = len(file_path.read_text(encoding="utf-8").splitlines())
        assert line_count <= 300, f"{file_path} has {line_count} lines"


def test_python_production_functions_stay_under_hard_size_caps() -> None:
    root = Path("packages/backend/src")
    for file_path in root.rglob("*.py"):
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                start_line = node.lineno
                end_line = getattr(node, "end_lineno", start_line)
                line_count = end_line - start_line + 1
                assert line_count <= 60, f"{file_path}:{node.name} has {line_count} lines"
