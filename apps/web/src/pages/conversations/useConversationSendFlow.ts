import { useState } from "react";

import type { ChatSendResponse } from "../../entities/chat/chat.types";
import { useCreateRunMutation } from "../../entities/run/run.api";
import { useSendChatMessageMutation } from "../../entities/chat/chat.api";
import {
  CUSTOM_MODEL_VALUE,
  DEFAULT_MODEL,
} from "../../features/chat_composer/chatComposer.constants";

export type SendMessageOptions = {
  forcePipeline?: boolean;
  allowRunStart?: boolean;
};

type UseConversationSendFlowOptions = {
  conversationId: string;
  onRunCreated: (runId: string) => void;
};

type ComposerState = {
  draft: string;
  isTyping: boolean;
  webSearching: boolean;
  selectedModel: string;
  customModel: string;
  runPipelineArmed: boolean;
  setDraft: (value: string) => void;
  setIsTyping: (value: boolean) => void;
  setWebSearching: (value: boolean) => void;
  setSelectedModel: (value: string) => void;
  setCustomModel: (value: string) => void;
  setRunPipelineArmed: (
    value: boolean | ((current: boolean) => boolean),
  ) => void;
};

function getRunStartPendingAction(
  response: ChatSendResponse,
): { type: "start_research_run"; prompt: string } | null {
  const pending = response.pending_action;
  if (
    !pending ||
    typeof pending !== "object" ||
    pending["type"] !== "start_research_run" ||
    typeof pending["prompt"] !== "string"
  ) {
    return null;
  }
  return {
    type: "start_research_run",
    prompt: pending["prompt"],
  };
}

function shouldStartRun(
  allowRunStart: boolean,
  response: ChatSendResponse,
) {
  return Boolean(
    allowRunStart &&
    response.assistant_message?.type === "run_started" &&
    getRunStartPendingAction(response),
  );
}

async function startRunFromResponse(
  response: ChatSendResponse,
  createRun: ReturnType<typeof useCreateRunMutation>,
  onRunCreated: (runId: string) => void,
) {
  const pendingAction = getRunStartPendingAction(response);
  if (!pendingAction) {
    throw new Error("Run start payload was missing from the chat response.");
  }
  const run = await createRun.mutateAsync({
    request_text: pendingAction.prompt,
    source_message_id: response.user_message?.id ?? undefined,
  });
  onRunCreated(run.run.id);
}

function resolveModel(selectedModel: string, customModel: string) {
  return selectedModel === CUSTOM_MODEL_VALUE ? customModel.trim() : selectedModel;
}

function useComposerState(): ComposerState {
  const [draft, setDraft] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [webSearching, setWebSearching] = useState(false);
  const [selectedModel, setSelectedModel] = useState(DEFAULT_MODEL);
  const [customModel, setCustomModel] = useState("");
  const [runPipelineArmed, setRunPipelineArmed] = useState(false);

  return {
    draft,
    isTyping,
    webSearching,
    selectedModel,
    customModel,
    runPipelineArmed,
    setDraft,
    setIsTyping,
    setWebSearching,
    setSelectedModel,
    setCustomModel,
    setRunPipelineArmed,
  };
}

function useMessageSender(
  conversationId: string,
  onRunCreated: (runId: string) => void,
  state: ComposerState,
) {
  const createRun = useCreateRunMutation(conversationId);
  const sendChat = useSendChatMessageMutation(conversationId, {
    onStatus: () => state.setWebSearching(true),
  });

  async function sendMessage(text: string, options: SendMessageOptions = {}) {
    const trimmed = text.trim();
    if (!trimmed) return;

    state.setIsTyping(true);
    try {
      const response = await sendChat.mutateAsync({
        conversation_id: conversationId,
        message: trimmed,
        client_message_id: crypto.randomUUID(),
        llm_model: resolveModel(state.selectedModel, state.customModel) || undefined,
        force_pipeline:
          options.forcePipeline !== undefined
            ? options.forcePipeline
            : state.runPipelineArmed && !trimmed.startsWith("__ACTION__:"),
      });

      if (!shouldStartRun(options.allowRunStart ?? false, response)) return;
      await startRunFromResponse(response, createRun, onRunCreated);
    } finally {
      state.setIsTyping(false);
      state.setWebSearching(false);
    }
  }

  return sendMessage;
}

export function useConversationSendFlow({
  conversationId,
  onRunCreated,
}: UseConversationSendFlowOptions) {
  const state = useComposerState();
  const sendMessage = useMessageSender(conversationId, onRunCreated, state);

  async function handleSend() {
    const text = state.draft.trim();
    if (!text || state.isTyping) return;

    await sendMessage(text, {
      forcePipeline: state.runPipelineArmed,
      allowRunStart: state.runPipelineArmed,
    });
    state.setDraft("");
    state.setRunPipelineArmed(false);
  }

  function handleAction(actionId: string) {
    void sendMessage(`__ACTION__:${actionId}`, {
      allowRunStart: actionId === "run_pipeline",
    });
  }

  return {
    ...state,
    sendMessage,
    handleSend,
    handleAction,
  };
}
