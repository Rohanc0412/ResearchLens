from researchlens.modules.evaluation.application import EvaluationProgressSink


class EvaluationGraphEventSink:
    async def info(self, *, key: str, message: str, payload: dict[str, object]) -> None:
        return None

    async def warning(self, *, key: str, message: str, payload: dict[str, object]) -> None:
        return None


class EvaluationGraphCheckpointSink:
    async def checkpoint(
        self,
        *,
        key: str,
        summary: dict[str, object],
        completed_stages: tuple[str, ...],
        next_stage: str | None,
    ) -> None:
        return None


class EvaluationGraphProgressWriter(EvaluationProgressSink):
    def __init__(self, events: EvaluationGraphEventSink) -> None:
        self._events = events

    async def section_started(self, *, section_title: str) -> None:
        await self._events.info(
            key=f"evaluate.section_started.{section_title}",
            message=f"Evaluating {section_title}",
            payload={"section_title": section_title},
        )

    async def section_completed(self, *, section_title: str) -> None:
        await self._events.info(
            key=f"evaluate.section_completed.{section_title}",
            message=f"Reviewed {section_title}",
            payload={"section_title": section_title},
        )
