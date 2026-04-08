from dataclasses import dataclass


@dataclass(frozen=True)
class WorkerBootstrapConfig:
    app_name: str = "researchlens-worker"
    phase: str = "phase-0"

