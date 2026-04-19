import { ArrowLeft } from "lucide-react";
import { Link } from "react-router-dom";

export function ChatViewHeader({
  title,
  projectId,
  projectName,
}: {
  title: string;
  projectId: string;
  projectName: string;
}) {
  return (
    <header className="legacy-chat-header">
      <div className="legacy-chat-header__content">
        <Link
          to={`/projects/${projectId}`}
          aria-label="Back to project"
          className="legacy-chat-header__back"
        >
          <ArrowLeft className="legacy-chat-header__back-icon" aria-hidden="true" />
        </Link>
        <div className="legacy-chat-header__copy">
          <h1 className="legacy-chat-header__title">{title}</h1>
          <p className="legacy-chat-header__subtitle">{projectName}</p>
        </div>
      </div>
    </header>
  );
}
