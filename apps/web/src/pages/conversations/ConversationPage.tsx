import { useEffect, useRef } from "react";
import { useSearchParams, useParams } from "react-router-dom";

import { useProjectQuery } from "../../entities/project/project.api";
import { ChatComposer } from "../../features/chat_composer/ChatComposer";
import { useChatMessagesQuery } from "../../entities/chat/chat.api";
import { useConversationQuery } from "../../entities/conversation/conversation.api";
import { ChatMessageList } from "../../widgets/conversation_shell/ChatMessageList";
import { ChatViewHeader } from "../../widgets/conversation_shell/ChatViewHeader";
import { ReportPane } from "../../widgets/conversation_shell/ReportPane";
import { useConversationSendFlow } from "./useConversationSendFlow";
import { useInitialConversationMessage } from "./useInitialConversationMessage";

export function ConversationPage() {
  const { projectId = "", conversationId = "" } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();

  const conversation = useConversationQuery(conversationId);
  const project = useProjectQuery(projectId);
  const messages = useChatMessagesQuery(conversationId);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const runId =
    searchParams.get("runId") ?? localStorage.getItem(`researchlens:last-run:${conversationId}`);
  const sendFlow = useConversationSendFlow({
    conversationId,
    onRunCreated: (nextRunId) => {
      localStorage.setItem(`researchlens:last-run:${conversationId}`, nextRunId);
      setSearchParams({ runId: nextRunId });
    },
  });

  useInitialConversationMessage(conversationId, sendFlow.sendMessage);

  useEffect(() => {
    const node = messagesEndRef.current;
    if (node && typeof node.scrollIntoView === "function") {
      node.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages.data?.length]);

  return (
    <div className="legacy-conversation-shell">
      <section className="legacy-conversation-shell__chat">
        <ChatViewHeader
          title={conversation.data?.title ?? "Conversation"}
          projectId={projectId}
          projectName={project.data?.name ?? "Project"}
        />
        <div className="legacy-conversation-shell__timeline">
          <ChatMessageList
            messages={messages.data ?? []}
            isTyping={sendFlow.isTyping}
            webSearching={sendFlow.webSearching}
            isActionPending={sendFlow.isTyping}
            activeRunId={runId}
            messagesEndRef={messagesEndRef}
            onAction={sendFlow.handleAction}
          />
        </div>
        <div className="legacy-conversation-shell__composer">
          <ChatComposer
            draft={sendFlow.draft}
            isTyping={sendFlow.isTyping}
            runPipelineArmed={sendFlow.runPipelineArmed}
            selectedModel={sendFlow.selectedModel}
            customModel={sendFlow.customModel}
            onDraftChange={sendFlow.setDraft}
            onSend={() => void sendFlow.handleSend()}
            onTogglePipeline={() => sendFlow.setRunPipelineArmed((prev) => !prev)}
            onModelChange={sendFlow.setSelectedModel}
            onCustomModelChange={sendFlow.setCustomModel}
          />
        </div>
      </section>
      <aside className="legacy-conversation-shell__report">
        <ReportPane
          runId={runId}
          conversationId={conversationId}
          conversationTitle={conversation.data?.title ?? "Research report"}
        />
      </aside>
    </div>
  );
}
