from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Protocol

from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.ext.asyncio import AsyncSession


class TransactionManager(Protocol):
    @asynccontextmanager
    async def boundary(self) -> AsyncIterator[None]:
        yield

    async def rollback(self) -> None: ...


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

    async def rollback(self) -> None:
        if not self._session.in_transaction():
            return
        try:
            await self._session.rollback()
        except InvalidRequestError as exc:
            if "already in progress" not in str(exc).casefold():
                raise
