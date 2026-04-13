import {
  ProjectsService,
  type ProjectResponse,
} from "@researchlens/api-client";
import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import { useAuth } from "../../app/providers/AuthProvider";

export const projectKeys = {
  all: ["projects"] as const,
  detail: (projectId: string) => ["projects", projectId] as const,
};

export function useProjectsQuery() {
  const auth = useAuth();

  return useQuery({
    queryKey: projectKeys.all,
    queryFn: () =>
      auth.authorizedRequest(() => ProjectsService.listProjectsProjectsGet()),
    enabled: auth.status === "authenticated",
  });
}

export function useProjectQuery(projectId: string) {
  const auth = useAuth();

  return useQuery({
    queryKey: projectKeys.detail(projectId),
    queryFn: () =>
      auth.authorizedRequest(() => ProjectsService.getProjectProjectsProjectIdGet(projectId)),
    enabled: auth.status === "authenticated",
  });
}

export function useCreateProjectMutation() {
  const auth = useAuth();
  const client = useQueryClient();

  return useMutation({
    mutationFn: (payload: { name: string; description?: string | null }) =>
      auth.authorizedRequest(() => ProjectsService.createProjectProjectsPost(payload)),
    onSuccess: (project) => {
      client.setQueryData<ProjectResponse[] | undefined>(projectKeys.all, (current) =>
        current ? [project, ...current] : [project],
      );
    },
  });
}
