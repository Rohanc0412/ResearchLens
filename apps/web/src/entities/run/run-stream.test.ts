import { afterEach, beforeEach, expect, test, vi } from "vitest";

import { parseSseChunk, streamRunEvents } from "./run-stream";

const originalFetch = global.fetch;

beforeEach(() => {
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
  global.fetch = originalFetch;
});

test("parses a run event SSE chunk", () => {
  const parsed = parseSseChunk(
    'event: checkpoint.written\nid: 7\ndata: {"event_number":7,"status":"running","stage":"draft","display_status":"Running","display_stage":"Drafting","message":"Drafting","retry_count":0,"cancel_requested":false,"run_id":"run-1","event_type":"checkpoint.written","payload":null,"ts":"2026-04-13T12:00:00Z"}\n\n',
  );

  expect(parsed?.id).toBe(7);
  expect(parsed?.payload.display_stage).toBe("Drafting");
});

test("reconnects with Last-Event-ID until a terminal event is seen", async () => {
  const requests: Array<Record<string, string>> = [];
  const encoder = new TextEncoder();
  global.fetch = vi
    .fn()
    .mockResolvedValueOnce(
      new Response(
        new ReadableStream({
          start(controller) {
            controller.enqueue(
              encoder.encode(
                'event: checkpoint.written\nid: 1\ndata: {"event_number":1,"status":"running","stage":"retrieve","display_status":"Running","display_stage":"Retrieving","message":"Retrieving","retry_count":0,"cancel_requested":false,"run_id":"run-1","event_type":"checkpoint.written","payload":null,"ts":"2026-04-13T12:00:00Z"}\n\n',
              ),
            );
            controller.close();
          },
        }),
        { status: 200, headers: { "Content-Type": "text/event-stream" } },
      ),
    )
    .mockResolvedValueOnce(
      new Response(
        new ReadableStream({
          start(controller) {
            controller.enqueue(
              encoder.encode(
                'event: run.succeeded\nid: 2\ndata: {"event_number":2,"status":"succeeded","stage":"export","display_status":"Completed","display_stage":"Exporting","message":"Done","retry_count":0,"cancel_requested":false,"run_id":"run-1","event_type":"run.succeeded","payload":null,"ts":"2026-04-13T12:00:01Z"}\n\n',
              ),
            );
            controller.close();
          },
        }),
        { status: 200, headers: { "Content-Type": "text/event-stream" } },
      ),
    )
    .mockImplementation(async (_input, init) => {
      requests.push((init?.headers as Record<string, string>) ?? {});
      return new Response(null, { status: 500 });
    }) as typeof fetch;

  const events: number[] = [];
  const controller = new AbortController();
  const promise = streamRunEvents({
    accessToken: "token",
    getRefreshedAccessToken: async () => "token",
    onEvent: (event) => events.push(event.event_number),
    onError: () => undefined,
    runId: "run-1",
    signal: controller.signal,
  });

  await vi.runAllTimersAsync();
  await promise;

  expect(events).toEqual([1, 2]);
  expect(global.fetch).toHaveBeenCalledTimes(2);
});
