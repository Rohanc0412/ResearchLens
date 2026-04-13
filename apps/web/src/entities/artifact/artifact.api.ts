import {
  ArtifactsService,
  type ArtifactResponse,
} from "@researchlens/api-client";
import { useMutation, useQuery } from "@tanstack/react-query";

import { useAuth } from "../../app/providers/AuthProvider";
import { downloadArtifactBlob } from "../../shared/api/client";

export const artifactKeys = {
  list: (runId: string) => ["artifacts", runId] as const,
  detail: (artifactId: string) => ["artifacts", "detail", artifactId] as const,
};

export function useArtifactsQuery(runId: string) {
  const auth = useAuth();

  return useQuery({
    queryKey: artifactKeys.list(runId),
    queryFn: () =>
      auth.authorizedRequest(() => ArtifactsService.listRunArtifactsRunsRunIdArtifactsGet(runId)),
    enabled: auth.status === "authenticated" && Boolean(runId),
  });
}

export function useArtifactQuery(artifactId: string) {
  const auth = useAuth();

  return useQuery({
    queryKey: artifactKeys.detail(artifactId),
    queryFn: () =>
      auth.authorizedRequest(() => ArtifactsService.getArtifactArtifactsArtifactIdGet(artifactId)),
    enabled: auth.status === "authenticated" && Boolean(artifactId),
  });
}

export function useArtifactDownloadMutation() {
  const auth = useAuth();

  return useMutation({
    mutationFn: async (artifact: ArtifactResponse) =>
      downloadArtifactBlob(artifact.id, auth.accessToken, artifact.filename),
  });
}
