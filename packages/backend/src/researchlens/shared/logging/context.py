from contextvars import ContextVar, Token

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")
service_var: ContextVar[str] = ContextVar("service", default="researchlens")
tenant_id_var: ContextVar[str] = ContextVar("tenant_id", default="-")


def bind_request_id(request_id: str) -> Token[str]:
    return request_id_var.set(request_id)


def bind_service(service: str) -> Token[str]:
    return service_var.set(service)


def bind_tenant_id(tenant_id: str) -> Token[str]:
    return tenant_id_var.set(tenant_id)


def reset_request_id(token: Token[str]) -> None:
    request_id_var.reset(token)


def reset_service(token: Token[str]) -> None:
    service_var.reset(token)


def reset_tenant_id(token: Token[str]) -> None:
    tenant_id_var.reset(token)


def get_request_id() -> str:
    return request_id_var.get()


def get_service() -> str:
    return service_var.get()


def get_tenant_id() -> str:
    return tenant_id_var.get()
