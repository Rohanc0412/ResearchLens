import logging
from time import perf_counter
from uuid import uuid4

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from researchlens.shared.logging.context import (
    bind_request_id,
    reset_request_id,
)

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {key.decode().lower(): value.decode() for key, value in scope["headers"]}
        request_id = headers.get("x-request-id", str(uuid4()))
        method = scope["method"]
        path = scope["path"]
        token = bind_request_id(request_id)
        start = perf_counter()
        status_code = 500

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                mutable_headers = MutableHeaders(scope=message)
                mutable_headers["X-Request-ID"] = request_id
            await send(message)

        logger.info("request started method=%s path=%s", method, path)
        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration_ms = round((perf_counter() - start) * 1000)
            logger.info(
                "request finished method=%s path=%s status=%s duration=%sms",
                method,
                path,
                status_code,
                duration_ms,
            )
            reset_request_id(token)
