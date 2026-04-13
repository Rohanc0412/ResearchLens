# Streaming Protocol

Run progress is exposed through `GET /runs/{run_id}/events`.

## Modes

- Default JSON mode returns historical events ordered by `event_number`.
- SSE mode activates when `Accept: text/event-stream` is present.
- JSON mode accepts `after_event_number` for incremental polling.
- SSE reconnect uses `Last-Event-ID`.

## Event envelope

Every delivered event includes:

- `run_id`
- `event_number`
- `event_type`
- `status`
- `stage`
- `display_status`
- `display_stage`
- `message`
- `retry_count`
- `cancel_requested`
- `payload`
- `ts`

The envelope is frontend-ready. UI consumers should display `message`, `display_status`, and `display_stage` directly instead of translating raw backend enums.

Most retrieval, drafting, and evaluation progress notifications are delivered with `event_type="checkpoint.written"` and a stage-specific human-readable `message`. Clients should treat `message` and `payload` as the user-facing progress contract rather than expecting a custom `event_type` for every sub-step.

Phase 8 keeps the frontend-facing envelope stable while evaluation joins the LangGraph flow. Graph progress is translated into the same persisted `run_events` rows and therefore follows the same ordering, dedupe, JSON, and SSE replay rules as Phase 5.

## Ordering and replay guarantees

- Ordering is guaranteed per run, not globally.
- `event_number` is strictly increasing per run.
- Reconnect replay returns only events where `event_number > Last-Event-ID`.
- Event visibility is guaranteed only after the transaction that wrote the event commits.
- Duplicate logical events are prevented by server-side `event_key` dedupe, not by the client hiding duplicates.

## Keepalives and closure

- Idle SSE streams emit keepalive comments.
- Terminal runs keep the stream open for a short grace window so final committed events can arrive.
- After the grace window, terminal streams close cleanly and clients should stop reconnecting.

## Human-readable messages

Run events are written for users, not backend operators. Examples include:

- `Run created`
- `Waiting for an available worker`
- `Run started`
- `Searching for relevant sources`
- `Draft preparation started`
- `Draft evidence pack ready`
- `Draft section started`
- `Draft section completed`
- `Draft report assembled`
- `Starting grounding evaluation`
- `Evaluating Methods`
- `Reviewed Results`
- `Computed evaluation summary`
- `Evaluation completed: 2 sections marked for possible repair`
- `Repair completed`
- `Starting targeted repair reevaluation`
- `Progress saved`
- `Stopping after the current safe step`
- `Run stopped`
- `Retrying from the last saved step`
- `Retrying from drafting`
- `Run completed successfully`
