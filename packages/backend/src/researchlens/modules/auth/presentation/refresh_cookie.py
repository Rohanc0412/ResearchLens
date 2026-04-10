from fastapi import Request, Response

from researchlens.modules.auth.application import AuthTokenResult


def set_refresh_cookie(*, request: Request, response: Response, result: AuthTokenResult) -> None:
    settings = request.app.state.bootstrap.settings.auth
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=result.refresh_token,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
        expires=result.refresh_expires_at,
    )


def clear_refresh_cookie(*, request: Request, response: Response) -> None:
    settings = request.app.state.bootstrap.settings.auth
    response.delete_cookie(
        key=settings.refresh_cookie_name,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
    )
