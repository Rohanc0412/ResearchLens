# Module Boundaries

ResearchLens keeps backend and frontend boundaries explicit.

## Backend

- Modules use `domain`, `application`, `infrastructure`, `presentation`, and thin `orchestration` only when the module actually owns staged execution.
- `runs` remains the lifecycle owner and top-level LangGraph owner.
- `evidence` stays read-focused.
- `artifacts` owns artifact persistence, metadata, manifest generation, and downloads.
- Route handlers stay thin.
- Repositories stay narrow.
- Domain code does not import FastAPI, ORM rows, or provider SDKs.

## Frontend

The browser app uses the same ownership discipline:

- `app/` owns bootstrapping, providers, routing, and layouts.
- `pages/` compose route surfaces from widgets/features/entities and do not own transport details.
- `widgets/` compose product sections such as the project sidebar, run progress, artifact browser, and evidence panel.
- `features/` own user actions such as create-project and conversation composer flows.
- `entities/` own query keys, generated-client access, streaming logic, and domain-facing hooks.
- `shared/` contains only generic UI, env, formatting, and transport helpers.

## Client boundary rules

- The generated OpenAPI client is the primary transport surface.
- Thin handwritten adapters are allowed only for session retry handling, SSE consumption, and binary download behavior that the generated client cannot model directly.
- Query hooks stay near entity ownership instead of in one global `api.ts` or `hooks.ts`.
- Components do not construct raw fetch requests for normal JSON transport.

## Streaming boundary rules

- The backend owns ordering, replay semantics, keepalives, and terminal closure.
- The frontend owns only reconnect, dedupe by `event_number`, and presentation of `display_status`, `display_stage`, and `message`.
- The frontend must not reinterpret backend lifecycle semantics or invent local run states.
