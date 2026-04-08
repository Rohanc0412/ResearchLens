# Module Boundaries

ResearchLens backend code is expected to use explicit layers inside each module.

## Required layers

- `domain`: entities, value objects, invariants, and business policies.
- `application`: use cases, commands, queries, and workflow orchestration for a module.
- `infrastructure`: persistence, queues, storage, SDK adapters, ORM mappings, and external integrations.
- `presentation`: request parsing, auth checks, response shaping, transport concerns, and SSE delivery.
- `orchestration`: allowed only when a module truly owns staged execution. It must remain a thin coordinator instead of becoming a mixed-responsibility dump.

## Boundary constraints

- Route handlers must stay thin and must not contain workflow logic.
- Repositories must stay narrow and must not make business policy decisions.
- ORM or storage models must not leak into domain or presentation layers.
- Provider SDKs stay inside infrastructure adapters.
- Shared code must remain generic and cross-cutting only.

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

