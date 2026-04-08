from dataclasses import dataclass


@dataclass(frozen=True)
class ApiBootstrapConfig:
    app_name: str = "researchlens-api"
    phase: str = "phase-0"

