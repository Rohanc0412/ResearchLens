from researchlens.modules import artifacts, auth, conversations, drafting, evaluation
from researchlens.modules import evidence, projects, repair, retrieval, runs


def test_module_placeholders_are_importable() -> None:
    modules = [
        auth,
        projects,
        conversations,
        runs,
        retrieval,
        drafting,
        evaluation,
        repair,
        evidence,
        artifacts,
    ]
    assert len(modules) == 10

