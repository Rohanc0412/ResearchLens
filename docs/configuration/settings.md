# Settings

Backend configuration is centralized under `researchlens.shared.config` using `pydantic-settings`.

## Principles

- Settings are grouped by subsystem instead of being read ad hoc from scattered `os.getenv` calls.
- `packages/backend/pyproject.toml` is the canonical backend dependency source.
- `langgraph` is now a canonical backend dependency because research-run orchestration is graph-driven in production.
- API, worker, tests, and Alembic all load the same typed settings surface.
- Validation fails fast for incompatible or unsafe configuration combinations.

## Subsystems

- `app`: environment, debug flag, phase identifier, API host and port, worker name
- `database`: URL, echo flag, pooling defaults, startup migration toggle
- `bootstrap_actor`: retained typed settings group for older bootstrap context, no longer the normal protected-route identity path
- `auth`: auth enablement flags, JWT issuer/secret, access-token lifetime, refresh-cookie behavior, refresh/reset token secrets, password reset lifetime, TOTP MFA settings, registration toggle, dev-mode secret safety
- `smtp`: enablement, host, port, credentials, sender identity
- `retrieval`: feature toggles and safety limits
- `drafting`: section evidence-pack limits, section length targets, retry limits, and bounded concurrency
- `llm`: provider selection, GPT-5 nano model default, timeouts, structured output limits, and credentials
- `embeddings`: provider selection, text-embedding-3-small model default, batching/concurrency limits, credentials, and cache behavior
- `observability`: service name, log level, JSON logs, tracing toggle
- `queue`: backend mode, URL, polling interval, lease timing, claim batch size, and SSE keepalive/grace windows
- `storage`: local or S3 mode, local artifact root, bucket, endpoint

## Validation

Startup validation currently rejects at least these cases:

- production with insecure auth defaults
- production with in-memory queue backend
- production with local-only storage mode
- enabled LLM provider without credentials
- OpenAI embeddings without credentials
- drafting min/max word ranges that are internally inconsistent
- redis queue mode without a queue URL
- S3 storage mode without a bucket
- SMTP enabled without a host
- production with SQLite as the database backend
- production with auth dev bypass enabled
- production with password reset token secret left at the dev default
- invalid refresh cookie SameSite value

## Usage

Use `researchlens.shared.config.get_settings()` as the single settings entrypoint. Tests should reset the cache between scenarios with `reset_settings_cache()`.

Secrets are expected to be injected by Doppler at runtime. Application code still reads only environment variables; it does not depend on a Doppler SDK. `.env.example` is a reference template only.

## Phase 3 auth note

The Phase 2 `bootstrap_actor` settings are no longer the normal identity path for protected routes. Protected project routes now resolve an authenticated actor from the bearer access token through the auth runtime.

Important auth settings include:

- `AUTH_ACCESS_TOKEN_SECRET`
- `AUTH_REFRESH_TOKEN_SECRET`
- `AUTH_PASSWORD_RESET_TOKEN_SECRET`
- `AUTH_JWT_ISSUER`
- `AUTH_ACCESS_TOKEN_TTL_MINUTES`
- `AUTH_REFRESH_TOKEN_TTL_DAYS`
- `AUTH_REFRESH_COOKIE_NAME`
- `AUTH_REFRESH_COOKIE_SECURE`
- `AUTH_REFRESH_COOKIE_SAMESITE`
- `AUTH_ALLOW_REGISTER`
- `AUTH_PASSWORD_RESET_MINUTES`
- `AUTH_MFA_CHALLENGE_MINUTES`
- `AUTH_MFA_TOTP_ISSUER`
- `AUTH_MFA_TOTP_PERIOD_SECONDS`
- `AUTH_MFA_TOTP_DIGITS`
- `AUTH_MFA_TOTP_WINDOW`

Tests set `AUTH_REFRESH_COOKIE_SECURE=false` for local TestClient cookie flows. Production must not use the dev token secrets or dev bypass.

Queue settings include:

- `QUEUE_BACKEND`: `db`, `memory`, or `redis`; defaults to `db`
- `QUEUE_POLL_INTERVAL_SECONDS`: worker poll cadence
- `QUEUE_LEASE_SECONDS`: queue lease duration before reclaim is allowed
- `QUEUE_MAX_ATTEMPTS`: hard ceiling on queue claim attempts for the same queue item
- `QUEUE_BATCH_SIZE`: max claimed queue items per poll
- `QUEUE_SSE_KEEPALIVE_SECONDS`: idle SSE keepalive cadence
- `QUEUE_SSE_TERMINAL_GRACE_SECONDS`: terminal stream grace window
Queue note:

- The canonical queue backend is `db`.
- `redis` remains a validated settings option only; no external broker implementation is currently wired.
- SSE and worker timing settings stay safe for local startup and installed-package test execution.
- The worker now has an explicit stop path and exits its poll loop cleanly on shutdown signals instead of relying on abrupt process termination.
- Phase 7.5 did not add graph-specific environment variables. LangGraph wiring is internal and uses the existing queue, retrieval, drafting, LLM, and embedding settings surface.

Phase 6 retrieval settings include:

- `RETRIEVAL_ENABLED_PROVIDERS`: JSON array provider list; defaults to Paper Search MCP, PubMed, Europe PMC, OpenAlex, and arXiv
- `RETRIEVAL_PRIMARY_PROVIDER`: defaults to `paper_search_mcp`
- `RETRIEVAL_FALLBACK_PROVIDERS`: JSON array provider list; defaults to PubMed, Europe PMC, OpenAlex, and arXiv
- `RETRIEVAL_FALLBACK_THRESHOLD`: fallback trigger threshold; defaults to 5 normalized candidates
- `RETRIEVAL_MAX_SOURCES_PER_RUN`
- `RETRIEVAL_ALLOW_EXTERNAL_FETCH`: defaults to `false`; when disabled the provider registry stays offline with fake providers for local and test runs
- `RETRIEVAL_MAX_OUTLINE_SECTIONS`
- `RETRIEVAL_MAX_GLOBAL_QUERIES`
- `RETRIEVAL_MAX_QUERIES_PER_SECTION`
- `RETRIEVAL_MAX_GLOBAL_QUERIES_TOTAL`
- `RETRIEVAL_MAX_RESULTS_PER_PROVIDER_QUERY`
- `RETRIEVAL_MAX_CANDIDATES_AFTER_NORMALIZATION`
- `RETRIEVAL_MAX_CANDIDATES_SENT_TO_RERANK`
- `RETRIEVAL_MIN_SELECTED_SOURCES`
- `RETRIEVAL_MAX_SELECTED_SOURCES`
- `RETRIEVAL_MAX_CONCURRENT_PROVIDER_SEARCHES`
- `RETRIEVAL_MAX_CONCURRENT_ENRICHMENT_FETCHES`
- `RETRIEVAL_PROVIDER_TIMEOUT_SECONDS`
- `RETRIEVAL_STAGE_SOFT_TIME_BUDGET_SECONDS`
- ranking weights: `RETRIEVAL_RANKING_LEXICAL_WEIGHT`, `RETRIEVAL_RANKING_EMBEDDING_WEIGHT`, `RETRIEVAL_RANKING_RECENCY_WEIGHT`, and `RETRIEVAL_RANKING_CITATION_WEIGHT`
- `RETRIEVAL_DIVERSITY_PER_BUCKET_LIMIT`
- `RETRIEVAL_INGESTION_CHUNK_SIZE`
- `RETRIEVAL_INGESTION_CHUNK_OVERLAP`

LLM settings keep GPT-5 nano separate from embeddings:

- `LLM_PROVIDER`: typed values allow `disabled`, `openai`, or `anthropic`; the current runtime factory only wires the OpenAI adapter
- `LLM_MODEL`: defaults to `gpt-5-nano`
- `LLM_API_KEY`
- `LLM_BASE_URL`
- `LLM_TIMEOUT_SECONDS`
- `LLM_MAX_OUTPUT_TOKENS`
- `LLM_TEMPERATURE`
- `LLM_ENABLE_OUTLINE_GENERATION`
- `LLM_ENABLE_QUERY_PLANNING`

Drafting settings add:

- `DRAFTING_ENABLED`
- `DRAFTING_MAX_SECTIONS_PER_RUN`
- `DRAFTING_MAX_EVIDENCE_ITEMS_PER_SECTION`
- `DRAFTING_MAX_EVIDENCE_CHARS_PER_ITEM`
- `DRAFTING_SECTION_MIN_WORDS`
- `DRAFTING_SECTION_MAX_WORDS`
- `DRAFTING_SECTION_MAX_OUTPUT_TOKENS`
- `DRAFTING_CORRECTION_RETRY_COUNT`
- `DRAFTING_MAX_CONCURRENT_SECTION_PREPARATION`
- `DRAFTING_MAX_CONCURRENT_SECTION_DRAFTS`
- `DRAFTING_MAX_CONCURRENT_SECTION_PERSISTENCE`
- `DRAFTING_STAGE_TIMEOUT_SECONDS`

Recommended local usage:

```bash
doppler run -- python -m uv run --package researchlens-api python -m researchlens_api.main
doppler run -- python -m uv run --package researchlens-worker python -m researchlens_worker.main
doppler run -- python -m uv run --package researchlens-backend pytest packages/backend/tests
```

Embedding settings are separate:

- `EMBEDDINGS_PROVIDER`: typed values allow `disabled`, `openai`, or `local`; the current runtime factory only wires the OpenAI adapter
- `EMBEDDINGS_MODEL`: defaults to `text-embedding-3-small`
- `EMBEDDINGS_API_KEY`
- `EMBEDDINGS_BASE_URL`
- `EMBEDDINGS_CACHE_ENABLED`
- `EMBEDDINGS_BATCH_SIZE`
- `EMBEDDINGS_MAX_CONCURRENT_BATCHES`
- `EMBEDDINGS_TIMEOUT_SECONDS`
