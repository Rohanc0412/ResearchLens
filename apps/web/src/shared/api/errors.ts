import { ApiError } from "@researchlens/api-client";

type ErrorLikeBody = {
  detail?: string;
  code?: string;
};

export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError;
}

export function getErrorMessage(
  error: unknown,
  fallback = "Request failed. Please try again.",
) {
  if (isApiError(error)) {
    const body = error.body as ErrorLikeBody | undefined;
    return body?.detail ?? error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return fallback;
}
