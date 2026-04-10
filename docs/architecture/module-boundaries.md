# Module Boundaries

ResearchLens backend code uses explicit layers inside each module, and Phase 2 validates those boundaries with a real `projects` slice.

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
