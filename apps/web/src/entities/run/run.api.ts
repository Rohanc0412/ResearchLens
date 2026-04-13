import {
  RunsService,
  type CreateRunResponse,
  type RunEventResponse,
  type RunSummaryResponse,
} from "@researchlens/api-client";
import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";

import { useAuth } from "../../app/providers/AuthProvider";
import { getErrorMessage } from "../../shared/api/errors";
import { streamRunEvents } from "./run-stream";

export const runKeys = {
  detail: (runId: string) => ["runs", runId] as const,
  events: (runId: string) => ["runs", runId, "events"] as const,
};

export function useRunQuery(runId: string) {
  const auth = useAuth();

  return useQuery({
    queryKey: runKeys.detail(runId),
    queryFn: () => auth.authorizedRequest(() => RunsService.getRunRunsRunIdGet(runId)),
    enabled: auth.status === "authenticated" && Boolean(runId),
    refetchInterval: (query) =>
      query.state.data && ["succeeded", "failed", "canceled"].includes(query.state.data.status)
        ? false
        : 2500,
  });
}

export function useRunEventsQuery(runId: string) {
  const auth = useAuth();

  return useQuery({
    queryKey: runKeys.events(runId),
    queryFn: () =>
      auth.authorizedRequest(() =>
        RunsService.listOrStreamRunEventsRunsRunIdEventsGet(runId),
      ),
    enabled: auth.status === "authenticated" && Boolean(runId),
  });
}

export function useCreateRunMutation(conversationId: string) {
  const auth = useAuth();
  const client = useQueryClient();

  return useMutation({
    mutationFn: (payload: {
      request_text: string;
      source_message_id?: string | null;
      client_request_id?: string | null;
      output_type?: string;
    }) =>
      auth.authorizedRequest(() =>
        RunsService.createRunConversationsConversationIdRunsPost(conversationId, payload),
      ),
    onSuccess: (result: CreateRunResponse) => {
      client.setQueryData(runKeys.detail(result.run.id), result.run);
    },
  });
}

export function useCancelRunMutation(runId: string) {
  const auth = useAuth();
  const client = useQueryClient();

  return useMutation({
    mutationFn: () =>
      auth.authorizedRequest(() => RunsService.cancelRunRunsRunIdCancelPost(runId)),
    onSuccess: (run) => {
      client.setQueryData(runKeys.detail(runId), run);
    },
  });
}

export function useRetryRunMutation(runId: string) {
  const auth = useAuth();
  const client = useQueryClient();

  return useMutation({
    mutationFn: () =>
      auth.authorizedRequest(() => RunsService.retryRunRunsRunIdRetryPost(runId)),
    onSuccess: (run) => {
      client.setQueryData(runKeys.detail(runId), run);
    },
  });
}

function mergeEvents(events: RunEventResponse[]) {
  return Array.from(new Map(events.map((event) => [event.event_number, event])).values()).sort(
    (left, right) => left.event_number - right.event_number,
  );
}

export function useLiveRunTimeline(runId: string) {
  const auth = useAuth();
  const accessToken = auth.accessToken;
  const restoreSession = auth.restoreSession;
  const status = auth.status;
  const initialEvents = useRunEventsQuery(runId);
  const queryClient = useQueryClient();
  const [streamError, setStreamError] = useState<string | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (status !== "authenticated") {
      return;
    }

    const controller = new AbortController();
    const existing =
      queryClient.getQueryData<RunEventResponse[]>(runKeys.events(runId)) ?? [];
    const lastEventId = existing.at(-1)?.event_number;

    void streamRunEvents({
      accessToken,
      getRefreshedAccessToken: restoreSession,
      onConnectionChange: setConnected,
      onEvent: (event) => {
        setStreamError(null);
        queryClient.setQueryData<RunEventResponse[] | undefined>(
          runKeys.events(runId),
          (current) => mergeEvents([...(current ?? []), event]),
        );
        queryClient.setQueryData<RunSummaryResponse | undefined>(
          runKeys.detail(runId),
          (current) =>
            current
              ? {
                  ...current,
                  status: event.status,
                  current_stage: event.stage,
                  display_status: event.display_status,
                  display_stage: event.display_stage,
                  retry_count: event.retry_count,
                  cancel_requested: event.cancel_requested,
                  last_event_number: event.event_number,
                }
              : current,
        );
      },
      onError: (error) => setStreamError(error.message),
      runId,
      signal: controller.signal,
      startAfterEventId: lastEventId,
    }).catch((error) => {
      setStreamError(getErrorMessage(error, "Run stream failed."));
      setConnected(false);
    });

    return () => controller.abort();
  }, [accessToken, queryClient, restoreSession, runId, status]);

  return useMemo(
    () => ({
      events: mergeEvents(initialEvents.data ?? []),
      isLoading: initialEvents.isLoading,
      isConnected: connected,
      error: streamError,
    }),
    [connected, initialEvents.data, initialEvents.isLoading, streamError],
  );
}
