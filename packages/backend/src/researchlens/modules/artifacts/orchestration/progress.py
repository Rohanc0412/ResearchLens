from typing import Protocol


class ArtifactExportEventSink(Protocol):
    async def info(self, *, key: str, message: str, payload: dict[str, object]) -> None: ...

    async def warning(self, *, key: str, message: str, payload: dict[str, object]) -> None: ...


class ArtifactExportCheckpointSink(Protocol):
    async def checkpoint(
        self,
        *,
        key: str,
        summary: dict[str, object],
        completed_stages: tuple[str, ...],
        next_stage: str | None,
    ) -> None: ...
