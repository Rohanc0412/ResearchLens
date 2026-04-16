export type ChatMessageType =
  | "chat"
  | "pipeline_offer"
  | "action"
  | "run_started"
  | "error"
  | "text";

export type ChatRole = "user" | "assistant" | "system";

export type ChatMessage = {
  id: string;
  role: ChatRole;
  type: ChatMessageType;
  content_text: string | null;
  content_json: Record<string, unknown> | null;
  created_at: string;
  client_message_id?: string | null;
  optimistic?: boolean;
};

export type ChatSendResponse = {
  conversation_id: string;
  user_message: ChatMessage | null;
  assistant_message: ChatMessage | null;
  pending_action: Record<string, unknown> | null;
  idempotent_replay: boolean;
};

export type PipelineOfferAction = {
  id: string;
  label: string;
};

export type PipelineOffer = {
  prompt_preview?: string;
  actions?: PipelineOfferAction[];
};
