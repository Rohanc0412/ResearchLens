import { ConversationsService, MessagesService, RunsService } from "@researchlens/api-client";
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { useAuth } from "../../app/providers/AuthProvider";
import { useConversationsQuery } from "../../entities/conversation/conversation.api";
import { useProjectQuery } from "../../entities/project/project.api";
import { titleFromPrompt } from "../../shared/lib/format";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";
import { EmptyState } from "../../shared/ui/EmptyState";
import { Page } from "../../shared/ui/Page";
import { Textarea } from "../../shared/ui/Textarea";

export function ProjectDetailPage() {
  const { projectId = "" } = useParams();
  const auth = useAuth();
  const navigate = useNavigate();
  const project = useProjectQuery(projectId);
  const conversations = useConversationsQuery(projectId);
  const [prompt, setPrompt] = useState("");
  const [launching, setLaunching] = useState(false);

  const launchConversation = async () => {
    setLaunching(true);
    try {
      const conversation = await auth.authorizedRequest(() =>
        ConversationsService.createConversationProjectsProjectIdConversationsPost(projectId, {
          title: titleFromPrompt(prompt),
        }),
      );
      const message = await auth.authorizedRequest(() =>
        MessagesService.postMessageConversationsConversationIdMessagesPost(conversation.id, {
          role: "user",
          type: "text",
          content_text: prompt,
          client_message_id: crypto.randomUUID(),
        }),
      );
      const run = await auth.authorizedRequest(() =>
        RunsService.createRunConversationsConversationIdRunsPost(conversation.id, {
          request_text: prompt,
          source_message_id: message.id,
          output_type: "report",
        }),
      );
      localStorage.setItem(`researchlens:last-run:${conversation.id}`, run.run.id);
      navigate(`/projects/${projectId}/conversations/${conversation.id}?runId=${run.run.id}`);
    } finally {
      setLaunching(false);
    }
  };

  return (
    <Page
      eyebrow="Project"
      title={project.data?.name ?? "Project"}
      subtitle={project.data?.description ?? "Create or continue conversations in this project."}
    >
      <div className="project-detail-grid">
        <Card className="prompt-launcher" title="Start a conversation" meta="Project-level launchpad">
          <div className="stack">
            <Textarea
              label="Research prompt"
              value={prompt}
              rows={6}
              onChange={(event) => setPrompt(event.target.value)}
            />
            <div className="row">
              <Button
                variant="primary"
                loading={launching}
                disabled={!prompt.trim()}
                onClick={() => void launchConversation()}
              >
                Open and run
              </Button>
            </div>
          </div>
        </Card>

        <Card className="workspace-panel" title="Recent conversations" meta={`${conversations.data?.length ?? 0} visible`}>
          {(conversations.data?.length ?? 0) === 0 ? (
            <EmptyState
              title="No conversations yet"
              body="Start a prompt-driven conversation to create the first research run."
            />
          ) : (
            <div className="data-list">
              {(conversations.data ?? []).map((conversation) => (
                <Link
                  key={conversation.id}
                  className="data-row"
                  to={`/projects/${projectId}/conversations/${conversation.id}`}
                >
                  <Card interactive className="data-row__card" title={conversation.title}>
                    <div className="meta-line">
                      Last message{" "}
                      {conversation.last_message_at
                        ? new Date(conversation.last_message_at).toLocaleString()
                        : "pending"}
                    </div>
                  </Card>
                </Link>
              ))}
            </div>
          )}
        </Card>
      </div>
    </Page>
  );
}
