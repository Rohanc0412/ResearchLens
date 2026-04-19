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
  pending_action: ChatPendingAction | null;
  idempotent_replay: boolean;
};

export type ResearchRunOfferAction = {
  type: "research_run_offer";
  prompt: string;
  created_at: string;
  ambiguous_count: number;
  llm_model?: string;
};

export type StartResearchRunAction = {
  type: "start_research_run";
  prompt: string;
};

export type ChatPendingAction =
  | ResearchRunOfferAction
  | StartResearchRunAction
  | Record<string, unknown>;

export type PipelineOfferAction = {
  id: string;
  label: string;
};

export type PipelineOffer = {
  prompt_preview?: string;
  actions?: PipelineOfferAction[];
};

export type ConversationLaunchState = {
  initialMessage?: string;
  runPipeline?: boolean;
};
