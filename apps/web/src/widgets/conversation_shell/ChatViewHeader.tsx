import { Link } from "react-router-dom";

import { Button } from "../../shared/ui/Button";

export function ChatViewHeader({
  title,
  projectId,
  messageCount,
  runId,
}: {
  title: string;
  projectId: string;
  messageCount: number;
  runId?: string | null;
}) {
  return (
    <header className="conversation-header">
      <div>
        <div className="eyebrow">Research workspace</div>
        <h1 className="display-heading conversation-header__title">{title}</h1>
        <div className="meta-line">
          Project {projectId} | {messageCount} persisted messages
        </div>
      </div>
      <div className="row">
        {runId ? (
          <Link to={`/runs/${runId}/artifacts`}>
            <Button compact variant="ghost">
              Review artifacts
            </Button>
          </Link>
        ) : null}
        <Link to={`/projects/${projectId}`}>
          <Button compact variant="secondary">
            Project
          </Button>
        </Link>
      </div>
    </header>
  );
}
