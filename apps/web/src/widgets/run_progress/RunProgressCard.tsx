import { useState } from "react";

import {
  useCancelRunMutation,
  useLiveRunTimeline,
  useRetryRunMutation,
  useRunQuery,
} from "../../entities/run/run.api";
import { ErrorBanner } from "../../shared/ui/ErrorBanner";
import { buildRunProgressModel } from "./buildRunProgressModel";
import { ResearchProgressCard } from "./ResearchProgressCard";

export function RunProgressCard({
  runId,
  conversationTitle,
}: {
  runId: string;
  conversationTitle?: string;
}) {
  const [expanded, setExpanded] = useState(false);
  const run = useRunQuery(runId);
  const timeline = useLiveRunTimeline(runId);
  const cancel = useCancelRunMutation(runId);
  const retry = useRetryRunMutation(runId);

  if (run.isLoading) {
    return (
      <div className="legacy-progress-card legacy-progress-card--loading">Loading run state...</div>
    );
  }
  if (run.error || !run.data) {
    return <ErrorBanner body="Run progress could not be loaded." />;
  }

  return (
    <ResearchProgressCard
      model={buildRunProgressModel(run.data, timeline.events, conversationTitle)}
      expanded={expanded}
      onToggleExpanded={() => setExpanded((current) => !current)}
      onCancel={run.data.can_stop ? () => void cancel.mutateAsync() : undefined}
      onRetry={run.data.can_retry ? () => void retry.mutateAsync() : undefined}
      runId={runId}
    />
  );
}
