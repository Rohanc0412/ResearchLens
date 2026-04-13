from sqlalchemy.engine import make_url

from researchlens.shared.config.settings_types import ResearchLensSettings


class InvalidSettingsError(ValueError):
    """Raised when cross-setting validation fails."""


def validate_settings(settings: ResearchLensSettings) -> None:
    errors: list[str] = []
    _validate_production_settings(settings, errors)
    _validate_provider_settings(settings, errors)
    _validate_retrieval_settings(settings, errors)
    _validate_drafting_settings(settings, errors)
    _validate_shared_runtime_settings(settings, errors)

    if errors:
        raise InvalidSettingsError(" ".join(errors))


def _validate_production_settings(
    settings: ResearchLensSettings,
    errors: list[str],
) -> None:
    if settings.app.environment == "production":
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


def _validate_provider_settings(
    settings: ResearchLensSettings,
    errors: list[str],
) -> None:
    if settings.llm.provider != "disabled" and not settings.llm.api_key:
        errors.append("LLM_API_KEY is required when LLM_PROVIDER is enabled.")

    if settings.embeddings.provider == "openai" and not settings.embeddings.api_key:
        errors.append("EMBEDDINGS_API_KEY is required when EMBEDDINGS_PROVIDER=openai.")
    if (
        settings.drafting.enabled
        and settings.llm.provider != "disabled"
        and not settings.llm.api_key
    ):
        errors.append(
            "LLM_API_KEY is required when drafting is enabled with an active LLM provider."
        )
    if settings.repair.enabled and settings.llm.provider != "disabled" and not settings.llm.api_key:
        errors.append("LLM_API_KEY is required when repair is enabled with an active LLM provider.")


def _validate_retrieval_settings(
    settings: ResearchLensSettings,
    errors: list[str],
) -> None:
    if settings.retrieval.enabled:
        if not settings.retrieval.enabled_providers:
            errors.append("RETRIEVAL_ENABLED_PROVIDERS must include at least one provider.")

        if settings.retrieval.primary_provider not in settings.retrieval.enabled_providers:
            errors.append("RETRIEVAL_PRIMARY_PROVIDER must be in RETRIEVAL_ENABLED_PROVIDERS.")

        if settings.retrieval.max_selected_sources < settings.retrieval.min_selected_sources:
            errors.append("RETRIEVAL_MAX_SELECTED_SOURCES must be >= MIN_SELECTED_SOURCES.")

        ranking_weight_total = (
            settings.retrieval.ranking_lexical_weight
            + settings.retrieval.ranking_embedding_weight
            + settings.retrieval.ranking_recency_weight
            + settings.retrieval.ranking_citation_weight
        )
        if ranking_weight_total <= 0:
            errors.append("At least one retrieval ranking weights value must be greater than zero.")


def _validate_drafting_settings(
    settings: ResearchLensSettings,
    errors: list[str],
) -> None:
    if settings.drafting.section_max_words < settings.drafting.section_min_words:
        errors.append("DRAFTING_SECTION_MAX_WORDS must be >= DRAFTING_SECTION_MIN_WORDS.")


def _validate_shared_runtime_settings(
    settings: ResearchLensSettings,
    errors: list[str],
) -> None:
    if settings.queue.backend == "redis" and not settings.queue.url:
        errors.append("QUEUE_URL is required when QUEUE_BACKEND=redis.")

    if settings.storage.mode == "s3" and not settings.storage.bucket:
        errors.append("STORAGE_BUCKET is required when STORAGE_MODE=s3.")

    if settings.smtp.enabled and not settings.smtp.host:
        errors.append("SMTP_HOST is required when SMTP_ENABLED=true.")

    if settings.auth.refresh_cookie_samesite not in {"lax", "strict", "none"}:
        errors.append("AUTH_REFRESH_COOKIE_SAMESITE must be lax, strict, or none.")

    database_url = make_url(settings.database.url)
    if settings.app.environment == "production" and database_url.get_backend_name() == "sqlite":
        errors.append("SQLite is not allowed as the production database backend.")
