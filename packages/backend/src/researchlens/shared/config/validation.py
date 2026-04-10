from sqlalchemy.engine import make_url

from researchlens.shared.config.settings_types import ResearchLensSettings


class InvalidSettingsError(ValueError):
    """Raised when cross-setting validation fails."""


def validate_settings(settings: ResearchLensSettings) -> None:
    errors: list[str] = []
    environment = settings.app.environment

    if environment == "production":
        if settings.auth.allow_insecure_dev_tokens:
            errors.append("AUTH_ALLOW_INSECURE_DEV_TOKENS must be false in production.")

        if settings.auth.access_token_secret == "dev-access-secret-change-me-32-bytes":
            errors.append("AUTH_ACCESS_TOKEN_SECRET must not use the dev default in production.")

        if settings.auth.refresh_token_secret == "dev-refresh-secret-change-me":
            errors.append("AUTH_REFRESH_TOKEN_SECRET must not use the dev default in production.")

        if settings.auth.password_reset_token_secret == "dev-password-reset-secret-change-me":
            errors.append(
                "AUTH_PASSWORD_RESET_TOKEN_SECRET must not use the dev default in production."
            )

        if settings.auth.dev_bypass_auth:
            errors.append("AUTH_DEV_BYPASS_AUTH must be false in production.")

        if settings.queue.backend == "memory":
            errors.append("QUEUE_BACKEND=memory is not allowed in production.")

        if settings.storage.mode == "local":
            errors.append("STORAGE_MODE=local is not allowed in production.")

    if settings.llm.provider != "disabled" and not settings.llm.api_key:
        errors.append("LLM_API_KEY is required when LLM_PROVIDER is enabled.")

    if settings.embeddings.provider == "openai" and not settings.embeddings.api_key:
        errors.append("EMBEDDINGS_API_KEY is required when EMBEDDINGS_PROVIDER=openai.")

    if settings.queue.backend == "redis" and not settings.queue.url:
        errors.append("QUEUE_URL is required when QUEUE_BACKEND=redis.")

    if settings.storage.mode == "s3" and not settings.storage.bucket:
        errors.append("STORAGE_BUCKET is required when STORAGE_MODE=s3.")

    if settings.smtp.enabled and not settings.smtp.host:
        errors.append("SMTP_HOST is required when SMTP_ENABLED=true.")

    if settings.auth.refresh_cookie_samesite not in {"lax", "strict", "none"}:
        errors.append("AUTH_REFRESH_COOKIE_SAMESITE must be lax, strict, or none.")

    database_url = make_url(settings.database.url)
    if environment == "production" and database_url.get_backend_name() == "sqlite":
        errors.append("SQLite is not allowed as the production database backend.")

    if errors:
        raise InvalidSettingsError(" ".join(errors))
