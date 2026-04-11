from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EmbeddingRequest:
    texts: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EmbeddingResult:
    vectors: tuple[tuple[float, ...], ...]
