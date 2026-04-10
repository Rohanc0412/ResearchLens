# Phase 4 Completion Report

## Phase title

Projects and conversations core

## Scope restatement

Phase 4 implemented project detail/update flows plus a dedicated `conversations` backend module for conversation CRUD, message persistence and reads, cursor-based conversation listing, and minimal conversation-scoped run-trigger recording. Full assistant generation, run execution internals, queueing, SSE, retrieval, drafting, evaluation, repair, and broader frontend rebuild work remained out of scope.

## Route and module layout summary

- `projects` now supports `GET /projects/{project_id}` and metadata updates through `PATCH /projects/{project_id}` while preserving existing create/list/delete behavior and deterministic same-name no-op semantics.
- `conversations` owns:
  - `POST /projects/{project_id}/conversations`
  - `GET /projects/{project_id}/conversations`
  - `GET /conversations/{conversation_id}`
  - `PATCH /conversations/{conversation_id}`
  - `DELETE /conversations/{conversation_id}`
- `messages` owns:
  - `POST /conversations/{conversation_id}/messages`
  - `GET /conversations/{conversation_id}/messages`
  - `GET /conversations/{conversation_id}/messages/{message_id}`
- `run triggers` owns:
  - `POST /conversations/{conversation_id}/run-triggers`

The conversations slice keeps domain, application, infrastructure, and presentation layers explicit. Message write/read flows are separate, repositories stay narrow, and no mixed `chat.py`-style orchestration file was introduced.

## Message model summary

- Messages are tenant-scoped and conversation-scoped.
- Each message stores `role`, `type`, `content_text`, optional `content_json`, optional `metadata_json`, `created_at`, and optional `client_message_id`.
- Message reads are chronological ascending by `created_at`, then `id`.
- Message posting updates the parent conversation `last_message_at`.
- Replays with the same `(tenant_id, conversation_id, client_message_id)` return the existing persisted message with `idempotent_replay=true` instead of creating duplicates.

## Persistence delivered

- Migration `20260410_0003_phase_4_conversations.py`
- Tables:
  - `conversations`
  - `messages`
  - `conversation_run_triggers`
- Indexes for project-scoped conversation listing, chronological message listing, and conversation-scoped run-trigger reads
- Cascade delete from conversations to messages and recorded run triggers

## Tests added or updated

- Unit tests for:
  - project metadata get/update flows
  - conversation title validation
  - message validation
  - conversation cursor encoding/decoding
  - conversation creation, message idempotency, and run-trigger validation use cases
- Integration tests for:
  - auth-protected project details and metadata updates
  - conversation CRUD
  - tenant/user scoping for conversation reads and lists
  - invalid project handling on conversation create
  - message post/list/get flows
  - message idempotent replay
  - `last_message_at` updates
  - delete conversation cascade behavior
  - run-trigger recording without real execution
  - migration upgrade coverage for the new schema

## Docs added or updated

- `README.md`
- `docs/architecture/system-overview.md`
- `docs/architecture/module-boundaries.md`
- `docs/architecture/conversations-module.md`
- `docs/phase_reports/phase_4_completion.md`

## Open design questions for Phase 5

- Whether run-trigger recording should remain conversation-owned once real run lifecycle state exists, or hand off immediately into a dedicated `runs` module aggregate.
- Whether run-trigger idempotency needs an explicit uniqueness policy on `client_request_id` before queue-backed execution begins.
- How project deletion should interact with future run records that may need longer-lived history than conversations/messages.
