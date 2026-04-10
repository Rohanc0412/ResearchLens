from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession


class TransactionManager(Protocol):
    @asynccontextmanager
    async def boundary(self) -> AsyncIterator[None]:
        yield


class SqlAlchemyTransactionManager:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @asynccontextmanager
    async def boundary(self) -> AsyncIterator[None]:
        try:
            yield
        except Exception:
            await self._session.rollback()
            raise
        else:
            await self._session.commit()
