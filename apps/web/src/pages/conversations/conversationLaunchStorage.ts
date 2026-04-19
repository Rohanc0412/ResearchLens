import type { ConversationLaunchState } from "../../entities/chat/chat.types";

const STORAGE_PREFIX = "researchlens:conversation-launch:";

function storageKey(conversationId: string) {
  return `${STORAGE_PREFIX}${conversationId}`;
}

export function persistConversationLaunchState(
  conversationId: string,
  state: ConversationLaunchState,
) {
  sessionStorage.setItem(storageKey(conversationId), JSON.stringify(state));
}

export function readConversationLaunchState(
  conversationId: string,
): ConversationLaunchState | null {
  const value = sessionStorage.getItem(storageKey(conversationId));
  if (!value) return null;

  try {
    return JSON.parse(value) as ConversationLaunchState;
  } catch {
    return null;
  }
}

export function clearConversationLaunchState(conversationId: string) {
  sessionStorage.removeItem(storageKey(conversationId));
}
