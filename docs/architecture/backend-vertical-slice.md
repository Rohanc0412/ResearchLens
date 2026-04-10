# Backend Vertical Slice

Phase 2 proves the rebuilt backend architecture with one small real module: `projects`.

## Why this slice exists

The goal is not feature breadth. The goal is to validate that the shared foundation and module boundaries work in real code:

- request-scoped logging and request IDs
- async DB runtime and session handling
- explicit transaction ownership
- shared error mapping
- migration-backed persistence
- thin FastAPI presentation
- application use cases that depend on ports
- infrastructure repositories that depend on SQLAlchemy only

## Projects module shape

`packages/backend/src/researchlens/modules/projects/` uses the required four-layer layout:

- `domain`: `Project` entity plus name validation and normalization
- `application`: use cases, DTOs, repository port, transaction port
- `infrastructure`: SQLAlchemy row, repository implementation, row-to-domain mapping, request runtime assembly
- `presentation`: FastAPI schemas, actor dependency, routes

The module currently exposes exactly four use cases:

- `create_project`
- `list_projects`
- `rename_project`
- `delete_project`

No later-phase runs, conversations, retrieval, or orchestration logic is mixed into this slice.

## Dependency direction

The intended dependency direction is visible in the code and enforced in tests:

- `presentation -> application`
- `application -> domain`
- `infrastructure -> application`
- `domain` does not import FastAPI or SQLAlchemy
- `presentation` does not import SQLAlchemy or module infrastructure
- shared code does not import business modules

Composition stays at the edges:

- `apps/api` wires logging, exception handling, routes, DB runtime, and the per-request projects runtime
- `apps/worker` wires logging and DB runtime only

## Temporary bootstrap actor

Auth is still out of scope in Phase 2, but the API routes still need tenant and actor identity to prove tenant-scoped behavior.

That temporary behavior lives in typed settings under `bootstrap_actor`:

- `BOOTSTRAP_ACTOR_ENABLED`
- `BOOTSTRAP_ACTOR_TENANT_ID`
- `BOOTSTRAP_ACTOR_USER_ID`

The projects presentation layer reads those settings through an explicit dependency and binds `tenant_id` into the logging context for the request. This is temporary bootstrap wiring, not the future auth design.
