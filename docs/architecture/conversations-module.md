# Conversations Module

Phase 4 introduces `researchlens.modules.conversations` as the backend owner of conversation, message, and conversation-scoped run-trigger intent persistence.

## Responsibilities

- Create, list, get, update, and delete tenant-scoped conversations.
- Persist and read tenant-scoped messages without assistant generation.
- Maintain `last_message_at` when messages are posted.
- Record minimal run-trigger intent from conversation context without executing a run.

## Layering

- `domain`: conversation, message, and run-trigger entities plus validation for titles, message content, message role/type, and trigger request text.
- `application`: focused commands and queries for conversation CRUD, message writes/reads, cursor handling, and run-trigger recording.
- `infrastructure`: SQLAlchemy rows, row mappers, narrow SQL repositories, a project-scope reader, and request-scoped runtime assembly.
- `presentation`: thin FastAPI routes and strict request/response models with `extra="forbid"`.

## Boundaries

- Message write and read flows stay separate. `POST /conversations/{conversation_id}/messages` does not classify intent, call providers, or generate assistant output.
- Run-trigger recording is separate from run execution. The module stores intent in `conversation_run_triggers` but does not create jobs, run lifecycle state, or SSE streams.
- The conversations module does not import the `projects` or `auth` business modules directly. Project existence is checked through a local infrastructure reader, and request identity is resolved through a presentation-owned auth runtime protocol.

## Persistence

- `conversations`: tenant id, optional project id, creator id, title, timestamps, and `last_message_at`.
- `messages`: tenant id, conversation id, role, type, text payload, structured JSON payload, metadata JSON, timestamp, and optional `client_message_id`.
- `conversation_run_triggers`: conversation context, optional origin message, normalized request text, optional client request id, creator id, status, and timestamp.

## API surface

- `POST /projects/{project_id}/conversations`
- `GET /projects/{project_id}/conversations`
- `GET /conversations/{conversation_id}`
- `PATCH /conversations/{conversation_id}`
- `DELETE /conversations/{conversation_id}`
- `POST /conversations/{conversation_id}/messages`
- `GET /conversations/{conversation_id}/messages`
- `GET /conversations/{conversation_id}/messages/{message_id}`
- `POST /conversations/{conversation_id}/run-triggers`

Conversation listing is project-scoped and sorted by `coalesce(last_message_at, created_at) desc` with cursor pagination. Message listing is chronological ascending. Message creation supports idempotent replay through `(tenant_id, conversation_id, client_message_id)`.
