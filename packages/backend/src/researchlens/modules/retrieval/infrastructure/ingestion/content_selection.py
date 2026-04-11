from dataclasses import dataclass
from hashlib import sha256


@dataclass(frozen=True, slots=True)
class IngestibleContent:
    text: str
    content_kind: str
    content_hash: str


def choose_ingestible_content(
    *,
    title: str | None,
    abstract: str | None,
    full_text: str | None,
) -> IngestibleContent:
    for kind, value in (
        ("full_text", full_text),
        ("abstract", abstract),
        ("title", title),
    ):
        if value and value.strip():
            text = value.strip()
            return IngestibleContent(
                text=text,
                content_kind=kind,
                content_hash=sha256(text.encode("utf-8")).hexdigest(),
            )
    raise ValueError("Selected source has no ingestible content.")
