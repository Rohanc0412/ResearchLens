import { useEffect, useRef } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import type { ConversationLaunchState } from "../../entities/chat/chat.types";
import type { SendMessageOptions } from "./useConversationSendFlow";
import {
  clearConversationLaunchState,
  readConversationLaunchState,
} from "./conversationLaunchStorage";

type SendInitialMessage = (
  text: string,
  options?: SendMessageOptions,
) => Promise<void>;

function readLaunchState(state: unknown): ConversationLaunchState | null {
  if (!state || typeof state !== "object") return null;
  return state as ConversationLaunchState;
}

export function useInitialConversationMessage(
  conversationId: string,
  sendMessage: SendInitialMessage,
) {
  const location = useLocation();
  const navigate = useNavigate();
  const initialMessageSentRef = useRef(false);
  const launchState =
    readConversationLaunchState(conversationId) ?? readLaunchState(location.state);
  const initialMessage = launchState?.initialMessage?.trim();
  const runPipeline = launchState?.runPipeline === true;

  useEffect(() => {
    if (!initialMessage || initialMessageSentRef.current) return;

    initialMessageSentRef.current = true;
    clearConversationLaunchState(conversationId);
    navigate(`${location.pathname}${location.search}${location.hash}`, {
      replace: true,
      state: {},
    });
    void sendMessage(initialMessage, {
      forcePipeline: runPipeline,
      allowRunStart: runPipeline,
    }).catch(() => {});
  }, [
    conversationId,
    initialMessage,
    location.hash,
    location.pathname,
    location.search,
    navigate,
    runPipeline,
    sendMessage,
  ]);
}
