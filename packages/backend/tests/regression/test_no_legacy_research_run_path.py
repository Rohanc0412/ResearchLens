from pathlib import Path


def test_legacy_research_run_stage_shell_files_are_removed() -> None:
    root = Path("packages/backend/src/researchlens")
    assert not (root / "modules/runs/application/stage_execution_controller.py").exists()
    assert not (root / "modules/runs/application/stage_progress_writers.py").exists()
    assert not (root / "modules/retrieval/orchestration/retrieval_stage_orchestrator.py").exists()
    assert not (root / "modules/drafting/orchestration/drafting_stage_orchestrator.py").exists()
