# Module Boundaries

ResearchLens backend code uses explicit layers inside each module. Phase 2 validated those boundaries with the `projects` slice, Phase 3 added `auth`, Phase 4 added `conversations`, and Phase 5 adds `runs` without turning routes, repositories, or worker entrypoints into mixed workflow files.

## Required layers

- `domain`: entities, value objects, invariants, and business policies.
- `application`: use cases, commands, queries, and workflow orchestration for a module.
- `infrastructure`: persistence, queues, storage, SDK adapters, ORM mappings, and external integrations.
- `presentation`: request parsing, auth checks, response shaping, transport concerns, and SSE delivery.
- `orchestration`: allowed only when a module truly owns staged execution. It must remain a thin coordinator instead of becoming a mixed-responsibility dump.

## Boundary constraints

- Route handlers must stay thin and must not contain workflow logic.
- Repositories must stay narrow and must not make business policy decisions.
- Transaction ownership must stay explicit. Repositories and routes do not commit or roll back.
- ORM or storage models must not leak into domain or presentation layers.
- Provider SDKs stay inside infrastructure adapters.
- Conversation, message, and run lifecycle responsibilities stay split across distinct use cases, routes, repositories, and queue/event stores. Do not recreate a mixed `chat.py` or `runner.py` flow.
- Auth crypto, JWT issuance, refresh token hashing, password reset token hashing, and mail delivery stay inside `auth.infrastructure`.
- Auth password policy and token/session invariants stay in `auth.domain` or `auth.application`, not in routes or shared helpers.
- Shared code must remain generic and cross-cutting only.
- API and worker entrypoint packages must not become alternate homes for business logic.
- Cross-module imports should be explicit and rare; default reach-through between modules is not allowed.

## Shared backend scope

Only the following shared backend folders are allowed:

- `shared/config`
- `shared/db`
- `shared/errors`
- `shared/events`
- `shared/ids`
- `shared/logging`
- `shared/time`

Business-specific logic does not belong in shared code.

## Enforcement

Phase 2 enforces this structure through `import-linter` plus backend-owned regression tests. The current regression checks cover:

- no cross-module business imports
- no FastAPI or SQLAlchemy ORM imports in domain layers
- no SQLAlchemy imports in presentation layers
- no direct infrastructure reach-through from presentation
- app entrypoints limited to composition-root imports rather than application or domain logic

Protected project routes now resolve request identity through a composition-owned auth runtime protocol instead of importing the auth module directly or reading `bootstrap_actor` settings.

Conversation, message, and run presentation code follows the same pattern: presentation depends on a composition-owned auth runtime protocol plus a request-scoped module runtime rather than reaching into auth infrastructure or shared DB helpers directly.

Phase 5 applies the same rule to `runs`: route handlers only authenticate, validate, call use cases, and host SSE transport; queue/event/checkpoint persistence stays in `runs.infrastructure`; retry floor rules, cancel semantics, and status transitions stay in `runs.application` and `runs.domain`.
