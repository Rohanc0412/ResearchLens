# Streaming Protocol

Run progress is exposed through `GET /runs/{run_id}/events`.

## Transport modes

- JSON history mode is the default.
- SSE mode activates when the client sends `Accept: text/event-stream`.
- JSON mode accepts `after_event_number`.
- SSE reconnect uses `Last-Event-ID`.

## Event envelope

Every run event includes:

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

Frontend consumers should treat `message`, `display_status`, and `display_stage` as the stable display contract.

## Replay and ordering

- Ordering is guaranteed per run.
- `event_number` is strictly increasing per run.
- Replay returns only events where `event_number > Last-Event-ID`.
- Server-side `event_key` dedupe prevents duplicate logical events at persistence time.

## Keepalive and closure

- Idle streams emit keepalive comments.
- Terminal runs stay open briefly so final committed events can flush.
- After terminal grace elapses, the server closes cleanly and clients should stop reconnecting.

## Frontend consumption rules

Phase 11 frontend behavior is:

- fetch JSON history first for durable replay
- open an authenticated SSE stream against the same route
- reconnect with `Last-Event-ID`
- merge events by `event_number`
- stop reconnecting after terminal closure
- surface backend-provided `can_stop`, `can_retry`, `cancel_requested`, `display_status`, and `display_stage` directly

The frontend does not invent local stage semantics or translate backend enums into a separate lifecycle model.
