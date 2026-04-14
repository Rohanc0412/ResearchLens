from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import pytest
from sqlalchemy.exc import InvalidRequestError

from researchlens.shared.db.transaction_manager import SqlAlchemyTransactionManager


class _SessionWithRollbackInProgress:
    def in_transaction(self) -> bool:
        return True

    async def rollback(self) -> None:
        raise InvalidRequestError(
            "Method 'rollback()' can't be called here; method 'rollback()' is already in progress."
        )


class _SessionWithoutTransaction:
    def __init__(self) -> None:
        self.rollback_calls = 0

    def in_transaction(self) -> bool:
        return False

    async def rollback(self) -> None:
        self.rollback_calls += 1


@pytest.mark.asyncio
async def test_transaction_manager_ignores_rollback_already_in_progress() -> None:
    manager = SqlAlchemyTransactionManager(_SessionWithRollbackInProgress())  # type: ignore[arg-type]

    await manager.rollback()


@pytest.mark.asyncio
async def test_transaction_manager_skips_rollback_without_active_transaction() -> None:
    session = _SessionWithoutTransaction()
    manager = SqlAlchemyTransactionManager(session)  # type: ignore[arg-type]

    await manager.rollback()

    assert session.rollback_calls == 0
