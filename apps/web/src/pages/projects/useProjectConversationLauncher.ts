import { useNavigate } from "react-router-dom";

import type { ConversationLaunchState } from "../../entities/chat/chat.types";
import { useCreateConversationMutation } from "../../entities/conversation/conversation.api";
import { titleFromPrompt } from "../../shared/lib/format";
import { persistConversationLaunchState } from "../conversations/conversationLaunchStorage";

function buildLaunchState(
  prompt: string,
  runPipeline: boolean,
): ConversationLaunchState {
  return { initialMessage: prompt, runPipeline };
}

export function useProjectConversationLauncher(projectId: string) {
  const navigate = useNavigate();
  const createConversation = useCreateConversationMutation(projectId);

  async function launchConversation(
    prompt: string,
    runPipeline: boolean,
  ): Promise<boolean> {
    const trimmedPrompt = prompt.trim();
    if (!trimmedPrompt) return false;

    const conversation = await createConversation.mutateAsync({
      title: titleFromPrompt(trimmedPrompt),
    });
    persistConversationLaunchState(
      conversation.id,
      buildLaunchState(trimmedPrompt, runPipeline),
    );
    navigate(`/projects/${projectId}/conversations/${conversation.id}`, {
      state: buildLaunchState(trimmedPrompt, runPipeline),
    });
    return true;
  }

  return {
    launchConversation,
    isLaunching: createConversation.isPending,
  };
}
