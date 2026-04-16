import { useEffect, useRef, useState } from "react";
import { useSearchParams, useParams } from "react-router-dom";

import { ChatComposer } from "../../features/chat_composer/ChatComposer";
import {
  CUSTOM_MODEL_VALUE,
  DEFAULT_MODEL,
} from "../../features/chat_composer/chatComposer.constants";
import { useChatMessagesQuery, useSendChatMessageMutation } from "../../entities/chat/chat.api";
import { useConversationQuery } from "../../entities/conversation/conversation.api";
import { useCreateRunMutation } from "../../entities/run/run.api";
import { ChatMessageList } from "../../widgets/conversation_shell/ChatMessageList";
import { ChatViewHeader } from "../../widgets/conversation_shell/ChatViewHeader";
import { ReportPane } from "../../widgets/conversation_shell/ReportPane";
import { RunProgressCard } from "../../widgets/run_progress/RunProgressCard";
import { Card } from "../../shared/ui/Card";

export function ConversationPage() {
  const { projectId = "", conversationId = "" } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();

  const conversation = useConversationQuery(conversationId);
  const messages = useChatMessagesQuery(conversationId);
  const createRun = useCreateRunMutation(conversationId);

  const [draft, setDraft] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [webSearching, setWebSearching] = useState(false);
  const [selectedModel, setSelectedModel] = useState(DEFAULT_MODEL);
  const [customModel, setCustomModel] = useState("");
  const [runPipelineArmed, setRunPipelineArmed] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const runId =
    searchParams.get("runId") ??
    localStorage.getItem(`researchlens:last-run:${conversationId}`);

  const sendChat = useSendChatMessageMutation(conversationId, {
    onStatus: () => setWebSearching(true),
  });

  // Auto-scroll when messages change
  useEffect(() => {
    const node = messagesEndRef.current;
    if (node && typeof node.scrollIntoView === "function") {
      node.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages.data?.length]);

  const resolvedModel =
    selectedModel === CUSTOM_MODEL_VALUE ? customModel.trim() : selectedModel;

  async function sendMessage(text: string, forcePipeline?: boolean) {
    const trimmed = text.trim();
    if (!trimmed) return;

    setIsTyping(true);
    try {
      const response = await sendChat.mutateAsync({
        conversation_id: conversationId,
        message: trimmed,
        client_message_id: crypto.randomUUID(),
        llm_model: resolvedModel || undefined,
        force_pipeline:
          forcePipeline !== undefined
            ? forcePipeline
            : runPipelineArmed && !trimmed.startsWith("__ACTION__:"),
      });

      // If backend signals a research run should start, create it
      const pending = response.pending_action;
      if (
        pending &&
        typeof pending === "object" &&
        pending["type"] === "start_research_run" &&
        typeof pending["prompt"] === "string"
      ) {
        const run = await createRun.mutateAsync({
          request_text: pending["prompt"],
          source_message_id: response.user_message?.id ?? undefined,
        });
        localStorage.setItem(`researchlens:last-run:${conversationId}`, run.run.id);
        setSearchParams({ runId: run.run.id });
      }
    } finally {
      setIsTyping(false);
      setWebSearching(false);
    }
  }

  function handleSend() {
    const text = draft.trim();
    if (!text || isTyping) return;
    void sendMessage(text).then(() => {
      setDraft("");
      setRunPipelineArmed(false);
    });
  }

  function handleQuickAction(action: string) {
    setDraft("");
    setRunPipelineArmed(false);
    void sendMessage(action, false);
  }

  function handleAction(actionId: string) {
    void sendMessage(`__ACTION__:${actionId}`);
  }

  return (
    <div className="conversation-workspace">
      <ChatViewHeader
        title={conversation.data?.title ?? "Conversation"}
        projectId={projectId}
        messageCount={messages.data?.length ?? 0}
        runId={runId}
      />
      <div className="conversation-workspace__grid">
        <div className="conversation-workspace__main">
          <ChatMessageList
            messages={messages.data ?? []}
            isTyping={isTyping}
            webSearching={webSearching}
            isActionPending={isTyping}
            activeRunId={runId}
            messagesEndRef={messagesEndRef}
            onAction={handleAction}
          />
          <div className="composer-dock">
            <ChatComposer
              draft={draft}
              isTyping={isTyping}
              runPipelineArmed={runPipelineArmed}
              selectedModel={selectedModel}
              customModel={customModel}
              onDraftChange={setDraft}
              onSend={handleSend}
              onQuickAction={handleQuickAction}
              onTogglePipeline={() => setRunPipelineArmed((prev) => !prev)}
              onModelChange={setSelectedModel}
              onCustomModelChange={setCustomModel}
            />
          </div>
        </div>
        <aside className="conversation-workspace__side">
          {runId ? (
            <RunProgressCard runId={runId} />
          ) : (
            <Card className="workspace-panel" title="Run status" meta="No active run">
              Start a research run from the composer to stream progress, evidence, and artifacts
              here.
            </Card>
          )}
          <ReportPane runId={runId} />
        </aside>
      </div>
    </div>
  );
}
