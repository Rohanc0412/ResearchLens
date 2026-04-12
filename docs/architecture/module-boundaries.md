# Module Boundaries

ResearchLens backend code uses explicit layers inside each module. Phase 7.5 keeps that modular-monolith shape while making LangGraph the only research-run orchestrator.

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
- The only intentional orchestration cross-module reach-through is `runs.orchestration` importing retrieval and drafting orchestration entrypoints so the top-level research-run graph can compose stage-local graph pieces.
- Retrieval application code depends on provider and ingestion ports. Provider adapters, persistence rows, and SDK/HTTP concerns stay under retrieval infrastructure.
- LLM and embedding provider details stay in shared provider-agnostic ports and isolated OpenAI adapter packages; retrieval orchestration does not import OpenAI SDK/response types.
- Drafting owns section briefs, allowed evidence packs, citation-token validation, per-section outputs, and report assembly. It consumes retrieval-owned persisted chunks as inputs through a drafting-owned input-reader port, not by importing retrieval or runs modules directly; worker composition remains the integration point.

## Shared backend scope

Only the following shared backend folders are allowed:

- `shared/config`
- `shared/db`
- `shared/errors`
- `shared/events`
- `shared/ids`
- `shared/llm`
- `shared/embeddings`
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

Phase 7.5 replaces the old stage-controller shell with a runs-owned LangGraph backbone:

- `runs.orchestration` owns graph state, routing, checkpoint/event bridges, cancel/resume mapping, and finalization
- `retrieval.orchestration` exposes graph-native retrieval nodes/subgraph wiring only
- `drafting.orchestration` exposes graph-native drafting nodes/subgraph wiring only
- retrieval and drafting business rules stay in their own application/domain/infrastructure layers
- worker composition remains a thin composition root and does not become a second orchestrator
