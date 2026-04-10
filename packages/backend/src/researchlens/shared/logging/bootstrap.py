import json
import logging
from typing import Any

from researchlens.shared.logging.context import (
    bind_service,
    get_request_id,
    get_service,
    get_tenant_id,
)


class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        record.service = get_service()
        record.tenant_id = get_tenant_id()
        return True


class KeyValueFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        parts = [message]
        request_id = getattr(record, "request_id", "-")
        tenant_id = getattr(record, "tenant_id", "-")
        if request_id != "-":
            parts.append(f"request_id={request_id}")
        if tenant_id != "-":
            parts.append(f"tenant_id={tenant_id}")
        return " ".join(parts)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "service": getattr(record, "service", "researchlens"),
            "message": record.getMessage(),
        }
        request_id = getattr(record, "request_id", "-")
        tenant_id = getattr(record, "tenant_id", "-")
        if request_id != "-":
            payload["request_id"] = request_id
        if tenant_id != "-":
            payload["tenant_id"] = tenant_id
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def configure_logging(*, service_name: str, level: str, json_logs: bool) -> None:
    root_logger = logging.getLogger()
    handler = logging.StreamHandler()
    formatter: logging.Formatter

    if json_logs:
        formatter = JsonFormatter()
    else:
        formatter = KeyValueFormatter("%(levelname)s %(service)s %(message)s")

    handler.setFormatter(formatter)
    handler.addFilter(ContextFilter())

    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(level.upper())

    for noisy_logger in ["sqlalchemy.engine", "uvicorn.access"]:
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)

    bind_service(service_name)
