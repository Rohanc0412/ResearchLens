import {
  ConversationsService,
  type ConversationResponse,
} from "@researchlens/api-client";
import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import { useAuth } from "../../app/providers/AuthProvider";

export const conversationKeys = {
  list: (projectId: string) => ["conversations", projectId] as const,
  detail: (conversationId: string) => ["conversations", "detail", conversationId] as const,
};

export function useConversationsQuery(projectId: string) {
  const auth = useAuth();

  return useQuery({
    queryKey: conversationKeys.list(projectId),
    queryFn: async () =>
      (
        await auth.authorizedRequest(() =>
          ConversationsService.listConversationsProjectsProjectIdConversationsGet(projectId),
        )
      ).items,
    enabled: auth.status === "authenticated" && Boolean(projectId),
  });
}

export function useConversationQuery(conversationId: string) {
  const auth = useAuth();

  return useQuery({
    queryKey: conversationKeys.detail(conversationId),
    queryFn: () =>
      auth.authorizedRequest(() =>
        ConversationsService.getConversationConversationsConversationIdGet(conversationId),
      ),
    enabled: auth.status === "authenticated" && Boolean(conversationId),
  });
}

export function useCreateConversationMutation(projectId: string) {
  const auth = useAuth();
  const client = useQueryClient();

  return useMutation({
    mutationFn: (payload: { title: string }) =>
      auth.authorizedRequest(() =>
        ConversationsService.createConversationProjectsProjectIdConversationsPost(
          projectId,
          payload,
        ),
      ),
    onSuccess: (conversation) => {
      client.setQueryData<ConversationResponse[] | undefined>(
        conversationKeys.list(projectId),
        (current) => (current ? [conversation, ...current] : [conversation]),
      );
      client.setQueryData(conversationKeys.detail(conversation.id), conversation);
    },
  });
}
