import { useMemo } from "react";
import { useSearchParams, useParams } from "react-router-dom";

import { ConversationComposer } from "../../features/post_message/ConversationComposer";
import { useConversationQuery } from "../../entities/conversation/conversation.api";
import { useMessagesQuery } from "../../entities/message/message.api";
import { useCreateRunMutation } from "../../entities/run/run.api";
import { Card } from "../../shared/ui/Card";
import { Page } from "../../shared/ui/Page";
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
    <Page
      eyebrow="Conversation"
      title={conversation.data?.title ?? "Conversation"}
      subtitle={`Project ${projectId} conversation history and research execution.`}
    >
      <div className="grid grid--2">
        <div className="stack">
          <Card title="Composer" meta="Post notes or start a research run">
            <ConversationComposer conversationId={conversationId} onResearch={startResearch} />
          </Card>
          <Card title="Messages" meta={`${messages.data?.length ?? 0} persisted`}>
            <div className="message-list">
              {(messages.data ?? []).map((message) => (
                <article key={message.id} className="message" data-role={message.role}>
                  <div className="row row--between">
                    <strong>{message.role}</strong>
                    <span className="meta-line">
                      {new Date(message.created_at).toLocaleString()}
                    </span>
                  </div>
                  <p>{message.content_text ?? JSON.stringify(message.content_json)}</p>
                </article>
              ))}
            </div>
          </Card>
        </div>

        <div className="stack">
          {runId ? (
            <RunProgressCard runId={runId} />
          ) : (
            <Card title="Run status" meta="No active run">
              Start a research run from the composer to stream progress, evidence, and artifacts here.
            </Card>
          )}
        </div>
      </div>
    </Page>
  );
}
