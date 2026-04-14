import re
from uuid import UUID

from researchlens.shared.errors import ValidationError

TOKEN_PATTERN = re.compile(
    r"\[\[chunk:(?P<chunk_id>[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})\]\]"
)
NORMALIZABLE_TOKEN_PATTERN = re.compile(
    r"(?i)(?<!\[)\[(?P<single_body>[^\[\]]*?"
    r"(?P<single_uuid>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"
    r"[^\[\]]*?)\](?!\])"
    r"|\[\[(?P<double_body>[^\[\]]*?"
    r"(?P<double_uuid>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"
    r"[^\[\]]*?)\]\]"
)


def normalize_citation_tokens(text: str) -> str:
    def _replace(match: re.Match[str]) -> str:
        chunk_id = match.group("single_uuid") or match.group("double_uuid")
        return f"[[chunk:{chunk_id.lower()}]]"

    return NORMALIZABLE_TOKEN_PATTERN.sub(_replace, text)


def parse_citation_tokens(text: str) -> tuple[UUID, ...]:
    return tuple(UUID(match.group("chunk_id")) for match in TOKEN_PATTERN.finditer(text))


def ensure_only_valid_citation_tokens(text: str) -> tuple[UUID, ...]:
    text = normalize_citation_tokens(text)
    malformed = re.findall(r"\[\[(?!chunk:)[^\]]+\]\]", text)
    if malformed:
        raise ValidationError("Section text contains malformed citation tokens.")
    return parse_citation_tokens(text)
