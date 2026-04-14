import { useMemo } from "react";
import { useSearchParams, useParams } from "react-router-dom";

import { ConversationComposer } from "../../features/post_message/ConversationComposer";
import { useConversationQuery } from "../../entities/conversation/conversation.api";
import { useMessagesQuery } from "../../entities/message/message.api";
import { useCreateRunMutation } from "../../entities/run/run.api";
import { Card } from "../../shared/ui/Card";
import { ChatMessageList } from "../../widgets/conversation_shell/ChatMessageList";
import { ChatViewHeader } from "../../widgets/conversation_shell/ChatViewHeader";
import { ReportPane } from "../../widgets/conversation_shell/ReportPane";
import { RunProgressCard } from "../../widgets/run_progress/RunProgressCard";

export function ConversationPage() {
  const { projectId = "", conversationId = "" } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const conversation = useConversationQuery(conversationId);
  const messages = useMessagesQuery(conversationId);
  const createRun = useCreateRunMutation(conversationId);
  const runId = useMemo(
    () =>
      searchParams.get("runId") ??
      localStorage.getItem(`researchlens:last-run:${conversationId}`),
    [conversationId, searchParams],
  );

  const startResearch = async ({
    text,
    sourceMessageId,
  }: {
    text: string;
    sourceMessageId: string;
  }) => {
    const run = await createRun.mutateAsync({
      request_text: text,
      source_message_id: sourceMessageId,
    });
    localStorage.setItem(`researchlens:last-run:${conversationId}`, run.run.id);
    setSearchParams({ runId: run.run.id });
  };

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
          <ChatMessageList messages={messages.data ?? []} />
          <div className="composer-dock">
            <ConversationComposer conversationId={conversationId} onResearch={startResearch} />
          </div>
        </div>
        <aside className="conversation-workspace__side">
          {runId ? (
            <RunProgressCard runId={runId} />
          ) : (
            <Card className="workspace-panel" title="Run status" meta="No active run">
              Start a research run from the composer to stream progress, evidence, and artifacts here.
            </Card>
          )}
          <ReportPane runId={runId} />
        </aside>
      </div>
    </div>
  );
}
