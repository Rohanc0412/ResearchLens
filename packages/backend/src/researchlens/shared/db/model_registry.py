from importlib import import_module

_ROW_MODULES = (
    "researchlens.modules.artifacts.infrastructure.rows",
    "researchlens.modules.auth.infrastructure.rows",
    "researchlens.modules.conversations.infrastructure.rows",
    "researchlens.modules.drafting.infrastructure.rows",
    "researchlens.modules.evaluation.infrastructure.rows",
    "researchlens.modules.projects.infrastructure.project_row",
    "researchlens.modules.repair.infrastructure.rows",
    "researchlens.modules.retrieval.infrastructure.persistence.rows",
    "researchlens.modules.runs.infrastructure.rows",
)


def register_db_models() -> None:
    for module_name in _ROW_MODULES:
        import_module(module_name)
