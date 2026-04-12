import re
from uuid import UUID

from researchlens.shared.errors import ValidationError

TOKEN_PATTERN = re.compile(
    r"\[\[chunk:(?P<chunk_id>[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})\]\]"
)


def parse_citation_tokens(text: str) -> tuple[UUID, ...]:
    return tuple(UUID(match.group("chunk_id")) for match in TOKEN_PATTERN.finditer(text))


def ensure_only_valid_citation_tokens(text: str) -> tuple[UUID, ...]:
    malformed = re.findall(r"\[\[(?!chunk:)[^\]]+\]\]", text)
    if malformed:
        raise ValidationError("Section text contains malformed citation tokens.")
    return parse_citation_tokens(text)
