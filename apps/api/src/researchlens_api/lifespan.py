from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from researchlens_api.bootstrap import build_api_bootstrap_state


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    state = build_api_bootstrap_state()
    app.state.bootstrap = state
    yield
    await state.database.dispose()
