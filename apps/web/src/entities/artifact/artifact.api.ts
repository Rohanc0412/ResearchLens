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
  text: (artifactId: string) => ["artifacts", "text", artifactId] as const,
};

export function useArtifactsQuery(
  runId: string,
  options?: {
    enabled?: boolean;
    refetchInterval?: number | false;
  },
) {
  const auth = useAuth();

  return useQuery({
    queryKey: artifactKeys.list(runId),
    queryFn: () =>
      auth.authorizedRequest(() => ArtifactsService.listRunArtifactsRunsRunIdArtifactsGet(runId)),
    enabled:
      auth.status === "authenticated" &&
      Boolean(runId) &&
      (options?.enabled ?? true),
    refetchInterval: options?.refetchInterval,
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

export function useArtifactTextQuery(
  artifactId: string,
  fallbackFilename?: string,
  options?: { enabled?: boolean },
) {
  const auth = useAuth();

  return useQuery({
    queryKey: [...artifactKeys.text(artifactId), fallbackFilename ?? ""],
    queryFn: async () => {
      const result = await downloadArtifactBlob(
        artifactId,
        auth.accessToken,
        fallbackFilename,
      );

      return {
        filename: result.filename,
        mediaType: result.mediaType,
        text: await result.blob.text(),
      };
    },
    enabled:
      auth.status === "authenticated" &&
      Boolean(artifactId) &&
      (options?.enabled ?? true),
  });
}
