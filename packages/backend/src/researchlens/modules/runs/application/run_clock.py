from datetime import UTC, datetime
from typing import Protocol


class RunClock(Protocol):
    def now(self) -> datetime: ...


class UtcRunClock:
    def now(self) -> datetime:
        return datetime.now(tz=UTC)
