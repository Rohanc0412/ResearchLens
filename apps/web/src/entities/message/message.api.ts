import {
  MessagesService,
  type MessageResponse,
  type PostMessageRequest,
} from "@researchlens/api-client";
import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import { useAuth } from "../../app/providers/AuthProvider";

export const messageKeys = {
  list: (conversationId: string) => ["messages", conversationId] as const,
};

export function useMessagesQuery(conversationId: string) {
  const auth = useAuth();

  return useQuery({
    queryKey: messageKeys.list(conversationId),
    queryFn: () =>
      auth.authorizedRequest(() =>
        MessagesService.listMessagesConversationsConversationIdMessagesGet(
          conversationId,
        ),
      ),
    enabled: auth.status === "authenticated" && Boolean(conversationId),
  });
}

export function usePostMessageMutation(conversationId: string) {
  const auth = useAuth();
  const client = useQueryClient();

  return useMutation({
    mutationFn: (payload: PostMessageRequest) =>
      auth.authorizedRequest(() =>
        MessagesService.postMessageConversationsConversationIdMessagesPost(
          conversationId,
          payload,
        ),
      ),
    onSuccess: (message) => {
      client.setQueryData<MessageResponse[] | undefined>(
        messageKeys.list(conversationId),
        (current) => (current ? [...current, message] : [message]),
      );
    },
  });
}
