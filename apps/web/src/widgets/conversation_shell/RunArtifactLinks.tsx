import { type ArtifactResponse } from "@researchlens/api-client";
import { Download, ExternalLink, FileText } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import {
  useArtifactDownloadMutation,
  useArtifactsQuery,
} from "../../entities/artifact/artifact.api";
import { useRunQuery } from "../../entities/run/run.api";
import { saveBlob } from "./reportPane.download";

type RunArtifactLinksProps = {
  runId: string;
  activeRunId?: string | null;
};

function formatArtifactLabel(artifact: ArtifactResponse) {
  const filename = artifact.filename.toLowerCase();
  if (filename.endsWith(".md")) return ".md";
  if (filename.endsWith(".pdf")) return ".pdf";
  if (filename.endsWith(".docx")) return ".docx";
  if (filename.endsWith(".html")) return ".html";
  if (filename.endsWith(".json")) return ".json";
  const extension = artifact.filename.split(".").pop()?.trim();
  return extension ? `.${extension.toLowerCase()}` : artifact.kind;
}

function sortArtifacts(artifacts: ArtifactResponse[]) {
  return [...artifacts].sort((left, right) => {
    const leftWeight = left.kind === "final_report_markdown" ? 0 : 1;
    const rightWeight = right.kind === "final_report_markdown" ? 0 : 1;
    if (leftWeight !== rightWeight) return leftWeight - rightWeight;
    return left.filename.localeCompare(right.filename);
  });
}

export function RunArtifactLinks({ runId, activeRunId }: RunArtifactLinksProps) {
  const run = useRunQuery(runId);
  const [shouldPoll, setShouldPoll] = useState(true);
  const artifacts = useArtifactsQuery(runId, {
    enabled: Boolean(runId),
    refetchInterval: shouldPoll ? 2500 : false,
  });
  const download = useArtifactDownloadMutation();
  const [downloadingIds, setDownloadingIds] = useState<Record<string, boolean>>({});

  const sortedArtifacts = sortArtifacts(artifacts.data ?? []);
  const hasArtifacts = sortedArtifacts.length > 0;
  const isTrackingCurrentRun =
    activeRunId === runId && !hasArtifacts && run.data?.status !== "failed" && run.data?.status !== "canceled";

  useEffect(() => {
    setShouldPoll(true);
  }, [runId]);

  useEffect(() => {
    if (hasArtifacts) {
      setShouldPoll(false);
      return;
    }
    if (run.data?.status === "failed" || run.data?.status === "canceled") {
      setShouldPoll(false);
    }
  }, [hasArtifacts, run.data?.status]);

  async function handleDownload(artifact: ArtifactResponse) {
    if (downloadingIds[artifact.id]) return;
    setDownloadingIds((current) => ({ ...current, [artifact.id]: true }));
    try {
      const result = await download.mutateAsync(artifact);
      saveBlob(result.blob, result.filename);
    } finally {
      setDownloadingIds((current) => ({ ...current, [artifact.id]: false }));
    }
  }

  if (!hasArtifacts) {
    if (!isTrackingCurrentRun) return null;
    return (
      <div className="legacy-chat-message__status-note">
        Tracking progress in the research report panel.
      </div>
    );
  }

  return (
    <div className="legacy-run-artifacts">
      <div className="legacy-run-artifacts__icon" aria-hidden="true">
        <FileText size={18} />
      </div>
      <div className="legacy-run-artifacts__body">
        <p className="legacy-run-artifacts__title">Research report</p>
        <p className="legacy-run-artifacts__subtitle">Run completed</p>
      </div>
      <div className="legacy-run-artifacts__actions">
        {sortedArtifacts.map((artifact) => (
          <button
            key={artifact.id}
            type="button"
            onClick={() => void handleDownload(artifact)}
            disabled={downloadingIds[artifact.id] === true}
            className="legacy-run-artifacts__download"
            aria-label={`Download ${formatArtifactLabel(artifact)}`}
          >
            <Download size={12} />
            {formatArtifactLabel(artifact)}
          </button>
        ))}
        <Link
          to={`/runs/${encodeURIComponent(runId)}/artifacts`}
          className="legacy-run-artifacts__link"
          aria-label="View all artifacts"
        >
          <ExternalLink size={14} />
        </Link>
      </div>
    </div>
  );
}
