import { OpenAPI } from "@researchlens/api-client";

import { env } from "../config/env";

export function configureApiClient(getAccessToken: () => string | null) {
  OpenAPI.BASE = env.apiBaseUrl;
  OpenAPI.WITH_CREDENTIALS = true;
  OpenAPI.CREDENTIALS = "include";
  OpenAPI.TOKEN = async () => getAccessToken() ?? "";
}

export async function downloadArtifactBlob(
  artifactId: string,
  accessToken: string | null,
  fallbackFilename?: string,
) {
  const response = await fetch(`${env.apiBaseUrl}/artifacts/${artifactId}/download`, {
    credentials: "include",
    headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : {},
  });

  if (!response.ok) {
    throw new Error(`Artifact download failed with status ${response.status}.`);
  }

  return {
    blob: await response.blob(),
    filename:
      response.headers
        .get("Content-Disposition")
        ?.match(/filename="(?<name>[^"]+)"/)
        ?.groups?.name ??
      fallbackFilename ??
      `artifact-${artifactId}`,
    mediaType: response.headers.get("Content-Type") ?? "application/octet-stream",
  };
}
