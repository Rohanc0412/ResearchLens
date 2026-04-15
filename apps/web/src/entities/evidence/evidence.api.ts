import {
  EvidenceService,
  EvaluationService,
  RepairService,
} from "@researchlens/api-client";
import { useQuery } from "@tanstack/react-query";

import { useAuth } from "../../app/providers/AuthProvider";
import { isApiErrorStatus } from "../../shared/api/errors";

export const evidenceKeys = {
  summary: (runId: string) => ["evidence", runId, "summary"] as const,
  section: (runId: string, sectionId: string) => ["evidence", runId, "sections", sectionId] as const,
  chunk: (chunkId: string) => ["evidence", "chunk", chunkId] as const,
  source: (sourceId: string) => ["evidence", "source", sourceId] as const,
  evaluation: (runId: string) => ["evaluation", runId] as const,
  issues: (runId: string) => ["evaluation", runId, "issues"] as const,
  repair: (runId: string) => ["repair", runId] as const,
};

export function useRunEvidenceSummaryQuery(runId: string) {
  const auth = useAuth();

  return useQuery({
    queryKey: evidenceKeys.summary(runId),
    queryFn: () =>
      auth
        .authorizedRequest(() => EvidenceService.getRunEvidenceRunsRunIdEvidenceGet(runId))
        .catch((error) => {
          if (isApiErrorStatus(error, 404)) {
            return null;
          }
          throw error;
        }),
    enabled: auth.status === "authenticated" && Boolean(runId),
  });
}

export function useSectionEvidenceQuery(runId: string, sectionId: string) {
  const auth = useAuth();

  return useQuery({
    queryKey: evidenceKeys.section(runId, sectionId),
    queryFn: () =>
      auth
        .authorizedRequest(() =>
          EvidenceService.getSectionEvidenceRunsRunIdEvidenceSectionsSectionIdGet(
            runId,
            sectionId,
          ),
        )
        .catch((error) => {
          if (isApiErrorStatus(error, 404)) {
            return null;
          }
          throw error;
        }),
    enabled: auth.status === "authenticated" && Boolean(runId) && Boolean(sectionId),
  });
}

export function useChunkDetailQuery(chunkId: string) {
  const auth = useAuth();

  return useQuery({
    queryKey: evidenceKeys.chunk(chunkId),
    queryFn: () =>
      auth.authorizedRequest(() =>
        EvidenceService.getChunkDetailEvidenceChunksChunkIdGet(chunkId),
      ),
    enabled: auth.status === "authenticated" && Boolean(chunkId),
  });
}

export function useSourceDetailQuery(sourceId: string) {
  const auth = useAuth();

  return useQuery({
    queryKey: evidenceKeys.source(sourceId),
    queryFn: () =>
      auth.authorizedRequest(() =>
        EvidenceService.getSourceDetailEvidenceSourcesSourceIdGet(sourceId),
      ),
    enabled: auth.status === "authenticated" && Boolean(sourceId),
  });
}

export function useEvaluationSummaryQuery(
  runId: string,
  options: { enabled?: boolean } = {},
) {
  const auth = useAuth();

  return useQuery({
    queryKey: evidenceKeys.evaluation(runId),
    queryFn: () =>
      auth
        .authorizedRequest(() => EvaluationService.getRunEvaluationRunsRunIdEvaluationGet(runId))
        .catch((error) => {
          if (isApiErrorStatus(error, 404)) {
            return null;
          }
          throw error;
        }),
    enabled: auth.status === "authenticated" && Boolean(runId) && (options.enabled ?? true),
  });
}

export function useEvaluationIssuesQuery(runId: string) {
  const auth = useAuth();

  return useQuery({
    queryKey: evidenceKeys.issues(runId),
    queryFn: () =>
      auth
        .authorizedRequest(() =>
          EvaluationService.listRunEvaluationIssuesRunsRunIdEvaluationIssuesGet(runId),
        )
        .catch((error) => {
          if (isApiErrorStatus(error, 404)) {
            return [];
          }
          throw error;
        }),
    enabled: auth.status === "authenticated" && Boolean(runId),
  });
}

export function useRepairSummaryQuery(runId: string) {
  const auth = useAuth();

  return useQuery({
    queryKey: evidenceKeys.repair(runId),
    queryFn: () =>
      auth.authorizedRequest(() => RepairService.getRunRepairRunsRunIdRepairGet(runId)),
    enabled: auth.status === "authenticated" && Boolean(runId),
  });
}
