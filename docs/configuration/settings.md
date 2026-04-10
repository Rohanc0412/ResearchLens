# Settings

Phase 2 centralizes backend configuration under `researchlens.shared.config` using `pydantic-settings`.

## Principles

- Settings are grouped by subsystem instead of being read ad hoc from scattered `os.getenv` calls.
- `packages/backend/pyproject.toml` is the canonical backend dependency source.
- API, worker, tests, and Alembic all load the same typed settings surface.
- Validation fails fast for incompatible or unsafe configuration combinations.

## Subsystems

- `app`: environment, debug flag, phase identifier, API host and port, worker name
- `database`: URL, echo flag, pooling defaults, startup migration toggle
- `bootstrap_actor`: temporary tenant and user identity for Phase 2 routes before auth exists
- `auth`: token secrets, token lifetimes, dev-mode secret safety
- `smtp`: enablement, host, port, credentials, sender identity
- `retrieval`: feature toggles and safety limits
- `llm`: provider selection and credentials
- `embeddings`: provider selection, model, credentials, cache behavior
- `observability`: service name, log level, JSON logs, tracing toggle
- `queue`: backend mode, URL, polling interval
- `storage`: local or S3 mode, local artifact root, bucket, endpoint

## Validation

Startup validation currently rejects at least these cases:

- production with insecure auth defaults
- production with in-memory queue backend
- production with local-only storage mode
- enabled LLM provider without credentials
- OpenAI embeddings without credentials
- redis queue mode without a queue URL
- S3 storage mode without a bucket
- SMTP enabled without a host
- production with SQLite as the database backend

## Usage

Use `researchlens.shared.config.get_settings()` as the single settings entrypoint. Tests should reset the cache between scenarios with `reset_settings_cache()`.

## Phase 2 bootstrap actor note

The `bootstrap_actor` settings are temporary composition support for pre-auth phases. They provide explicit default values for:

- tenant ID
- user ID

They are consumed through API presentation dependencies so tenant-scoped routes can behave realistically without introducing Phase 3 auth work. Treat this as replaceable bootstrap wiring, not as a permanent auth model.
