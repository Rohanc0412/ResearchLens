import re
from uuid import UUID

TOKEN_PATTERN = re.compile(
    r"\[\[chunk:(?P<chunk_id>[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12})\]\]"
)


def citation_tokens_for_text(text: str) -> tuple[UUID, ...]:
    return tuple(UUID(match.group("chunk_id")) for match in TOKEN_PATTERN.finditer(text))


def invalid_citation_ids(
    *,
    cited_chunk_ids: tuple[UUID, ...],
    allowed_chunk_ids: tuple[UUID, ...],
) -> tuple[UUID, ...]:
    allowed = frozenset(allowed_chunk_ids)
    return tuple(chunk_id for chunk_id in cited_chunk_ids if chunk_id not in allowed)
