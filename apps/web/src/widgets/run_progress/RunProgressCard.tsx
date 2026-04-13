import { motion, useReducedMotion } from "framer-motion";
import { Link } from "react-router-dom";

import {
  useCancelRunMutation,
  useLiveRunTimeline,
  useRetryRunMutation,
  useRunQuery,
} from "../../entities/run/run.api";
import { formatDateTime } from "../../shared/lib/format";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";
import { ErrorBanner } from "../../shared/ui/ErrorBanner";

function getRunProgress(status: string, stage: string | null) {
  if (status === "succeeded" || status === "failed" || status === "canceled") return 100;
  if (status === "queued") return 14;
  if (stage === "retrieve") return 30;
  if (stage === "draft") return 52;
  if (stage === "evaluate") return 72;
  if (stage === "repair") return 86;
  if (stage === "export") return 96;
  return 8;
}

export function RunProgressCard({ runId }: { runId: string }) {
  const reduceMotion = useReducedMotion();
  const run = useRunQuery(runId);
  const timeline = useLiveRunTimeline(runId);
  const cancel = useCancelRunMutation(runId);
  const retry = useRetryRunMutation(runId);

  if (run.isLoading) {
    return <Card title="Run progress">Loading run state...</Card>;
  }

  if (run.error || !run.data) {
    return <ErrorBanner body="Run progress could not be loaded." />;
  }

  const progress = getRunProgress(run.data.status, run.data.current_stage);

  return (
    <Card
      title="Run progress"
      meta={`${run.data.display_status} • ${run.data.display_stage} • updated ${formatDateTime(
        run.data.updated_at,
      )}`}
      actions={
        <div className="row">
          {run.data.can_stop ? (
            <Button compact variant="danger" onClick={() => void cancel.mutateAsync()}>
              Stop
            </Button>
          ) : null}
          {run.data.can_retry ? (
            <Button compact variant="secondary" onClick={() => void retry.mutateAsync()}>
              Retry
            </Button>
          ) : null}
        </div>
      }
    >
      <div className="stack">
        <div className="row row--between">
          <span className="pill">{timeline.isConnected ? "Live stream connected" : "Stream idle"}</span>
          {run.data.status === "succeeded" ? (
            <Link to={`/runs/${runId}/artifacts`}>
              <Button compact variant="primary">
                View artifacts
              </Button>
            </Link>
          ) : null}
        </div>
        <div className="run-progress__rail" aria-hidden="true">
          <motion.div
            className="run-progress__fill"
            animate={{ width: `${progress}%` }}
            initial={reduceMotion ? undefined : { width: "0%" }}
            transition={{ duration: 0.28 }}
          />
        </div>
        {timeline.error ? <ErrorBanner body={timeline.error} /> : null}
        <div className="event-log">
          {timeline.events.slice(-8).reverse().map((event) => (
            <motion.div
              key={event.event_number}
              className="card"
              initial={reduceMotion ? undefined : { opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <div className="card__body">
                <div className="row row--between">
                  <strong>{event.message}</strong>
                  <span className="meta-line">#{event.event_number}</span>
                </div>
                <div className="meta-line">
                  {event.display_status} • {event.display_stage} • {formatDateTime(event.ts)}
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </Card>
  );
}
