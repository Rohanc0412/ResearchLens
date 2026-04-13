import re
from uuid import UUID

from researchlens.modules.artifacts.domain.export_models import CitationReference, ExportChunk
from researchlens.shared.errors import ValidationError

_TOKEN_PATTERN = re.compile(
    r"\[\[chunk:(?P<chunk_id>[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12})\]\]"
)


def resolve_citations(
    *,
    section_texts: tuple[str, ...],
    chunks: tuple[ExportChunk, ...],
) -> tuple[CitationReference, ...]:
    chunk_by_id = {chunk.chunk_id: chunk for chunk in chunks}
    citations: list[CitationReference] = []
    seen: set[UUID] = set()
    for text in section_texts:
        _reject_malformed_tokens(text)
        for match in _TOKEN_PATTERN.finditer(text):
            chunk_id = UUID(match.group("chunk_id"))
            chunk = chunk_by_id.get(chunk_id)
            if chunk is None:
                raise ValidationError(f"Citation references unknown chunk {chunk_id}.")
            if chunk_id not in seen:
                seen.add(chunk_id)
                citations.append(
                    CitationReference(
                        citation_label=f"C{len(citations) + 1}",
                        chunk_id=chunk.chunk_id,
                        source_id=chunk.source_id,
                    )
                )
    return tuple(citations)


def replace_citation_tokens(text: str, citations: tuple[CitationReference, ...]) -> str:
    label_by_chunk = {item.chunk_id: item.citation_label for item in citations}

    def _replace(match: re.Match[str]) -> str:
        chunk_id = UUID(match.group("chunk_id"))
        return f"[{label_by_chunk[chunk_id]}]"

    return _TOKEN_PATTERN.sub(_replace, text)


def _reject_malformed_tokens(text: str) -> None:
    malformed = re.findall(r"\[\[(?!chunk:)[^\]]+\]\]", text)
    if malformed:
        raise ValidationError("Export found malformed citation tokens.")
