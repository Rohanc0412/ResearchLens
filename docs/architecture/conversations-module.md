# Conversations Module

The conversations module owns conversation persistence plus the chat workspace send flow. It can persist assistant-side chat artifacts such as quick answers, pipeline offers, and explicit run-start acknowledgements, but it does not own run lifecycle execution.

## Responsibilities

- Create, list, get, update, and delete tenant-scoped conversations.
- Persist and read tenant-scoped user and assistant messages for the conversation workspace.
- Route chat-send requests between quick answers, research-run offers, and explicit run-start acknowledgements.
- Maintain `last_message_at` when messages are posted.
- Provide conversation context that the runs module can validate before creating a run.

## Layering

- `domain`: conversation and message entities plus validation for titles, message content, and message role/type.
- `application`: focused commands and queries for conversation CRUD, message writes/reads, and cursor handling.
- `application`: focused commands and queries for conversation CRUD, message writes/reads, cursor handling, and chat intent routing.
- `infrastructure`: SQLAlchemy rows, row mappers, narrow SQL repositories, a project-scope reader, and request-scoped runtime assembly. The runs module reads conversation/message scope through local table readers rather than owning conversation lifecycle state.
- `presentation`: thin FastAPI routes and strict request/response models with `extra="forbid"`.

## Boundaries

- Message write and read flows stay separate. `POST /conversations/{conversation_id}/messages` does not classify intent, call providers, or generate assistant output.
- Run lifecycle moved out of the conversations slice in Phase 5. `POST /conversations/{conversation_id}/run-triggers` remains only as a compatibility alias implemented by the runs module.
- The conversations module does not import the `projects` or `auth` business modules directly. Project existence is checked through a local infrastructure reader, and request identity is resolved through a presentation-owned auth runtime protocol.

## Persistence

- `conversations`: tenant id, optional project id, creator id, title, timestamps, and `last_message_at`.
- `messages`: tenant id, conversation id, role, type, text payload, structured JSON payload, metadata JSON, timestamp, and optional `client_message_id`.
- `conversation_run_triggers`: retained Phase 4 compatibility data only. The table is no longer the lifecycle source of truth.

## API surface

- `POST /projects/{project_id}/conversations`
- `GET /projects/{project_id}/conversations`
- `GET /conversations/{conversation_id}`
- `PATCH /conversations/{conversation_id}`
- `DELETE /conversations/{conversation_id}`
- `POST /conversations/{conversation_id}/messages`
- `POST /conversations/{conversation_id}/send`
- `GET /conversations/{conversation_id}/messages`
- `GET /conversations/{conversation_id}/messages/{message_id}`
- `POST /conversations/{conversation_id}/run-triggers` is now a runs-module compatibility alias, not a conversations-module lifecycle flow.

Conversation listing is project-scoped and sorted by `coalesce(last_message_at, created_at) desc` with cursor pagination. Message listing is chronological ascending. Message creation supports idempotent replay through `(tenant_id, conversation_id, client_message_id)`.

`POST /conversations/{conversation_id}/send` can suggest a research run through a `pipeline_offer`, but only explicit UI-driven research selections such as `force_pipeline` or `run_pipeline` return a `start_research_run` pending action for the frontend to convert into a real run.
