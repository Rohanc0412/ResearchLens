from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class StructuredGenerationRequest:
    schema_name: str
    prompt: str
    system_prompt: str | None = None
    max_output_tokens: int | None = None


@dataclass(frozen=True, slots=True)
class StructuredGenerationResult:
    data: dict[str, Any]
    raw_text: str | None = None
