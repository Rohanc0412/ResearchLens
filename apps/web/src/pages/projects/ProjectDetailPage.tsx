import { ConversationsService, MessagesService, RunsService } from "@researchlens/api-client";
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { useAuth } from "../../app/providers/AuthProvider";
import { useConversationsQuery } from "../../entities/conversation/conversation.api";
import { useProjectQuery } from "../../entities/project/project.api";
import { titleFromPrompt } from "../../shared/lib/format";
import { Button } from "../../shared/ui/Button";
import { EmptyState } from "../../shared/ui/EmptyState";
import { Page } from "../../shared/ui/Page";

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
      eyebrow=""
      title={project.data?.name ?? "Project"}
      actions={
        <Button variant="primary" onClick={() => document.getElementById("project-prompt")?.focus()}>
          <span aria-hidden="true">+</span>
          New chat
        </Button>
      }
      centered
    >
      <section className="project-composer" aria-label="Start a chat">
        <textarea
          id="project-prompt"
          aria-label="Research question"
          placeholder="Ask a research question..."
          value={prompt}
          onChange={(event) => setPrompt(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey && prompt.trim()) {
              event.preventDefault();
              void launchConversation();
            }
          }}
        />
        <div className="project-composer__footer">
          <span>
            Press <kbd>Enter</kbd> to send, <kbd>Shift+Enter</kbd> for newline
          </span>
          <button className="project-composer__report" type="button">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M12 3v4" />
              <path d="m8 7 4-4 4 4" />
              <path d="M6 12.5v5.25A2.25 2.25 0 0 0 8.25 20h7.5A2.25 2.25 0 0 0 18 17.75V12.5" />
            </svg>
            Run research report
          </button>
          <Button
            variant="primary"
            loading={launching}
            disabled={!prompt.trim()}
            onClick={() => void launchConversation()}
          >
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="m4 11.5 15-7-7 15-2.2-5.3L4 11.5Z" />
            </svg>
            Start chat
          </Button>
        </div>
      </section>

      <section className="recent-sessions">
        <h2 className="eyebrow">Recent Sessions</h2>
        {(conversations.data?.length ?? 0) === 0 ? (
          <EmptyState
            icon="message"
            title="No sessions yet"
            body="Ask a research question above to start your first chat."
          />
        ) : (
          <div className="session-list">
            {(conversations.data ?? []).map((conversation) => (
              <Link
                key={conversation.id}
                className="session-row"
                to={`/projects/${projectId}/conversations/${conversation.id}`}
              >
                <strong>{conversation.title}</strong>
                <span className="meta-line">
                  {conversation.last_message_at
                    ? new Date(conversation.last_message_at).toLocaleString()
                    : "No messages yet"}
                </span>
              </Link>
            ))}
          </div>
        )}
      </section>
    </Page>
  );
}
