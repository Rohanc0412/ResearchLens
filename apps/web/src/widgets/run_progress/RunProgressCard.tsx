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
import { buildRunProgressModel } from "./buildRunProgressModel";

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

  const model = buildRunProgressModel(run.data, timeline.events);
  const streamStatus = timeline.isConnected
    ? "Live stream connected"
    : run.data.status === "succeeded" || run.data.status === "failed" || run.data.status === "canceled"
      ? "Run settled"
      : timeline.error
        ? "Stream reconnecting"
        : "Stream idle";

  return (
    <Card
      title="Run progress"
      meta={`${run.data.display_status} | ${run.data.display_stage} | updated ${formatDateTime(
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
      <div className="run-progress stack">
        <div className="run-progress__summary">
          <div>
            <div className="eyebrow">Current action</div>
            <strong>{model.currentAction}</strong>
          </div>
          <span className="pill">{streamStatus}</span>
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
            animate={{ width: `${model.progress}%` }}
            initial={reduceMotion ? undefined : { width: "0%" }}
            transition={{ duration: 0.28 }}
          />
        </div>
        <div className="run-progress__steps" aria-label="Run stages">
          {model.steps.map((step) => (
            <div key={step.key} className="run-progress__step" data-state={step.state}>
              <span className="run-progress__dot" />
              <div>
                <strong>{step.title}</strong>
                <p>{step.body}</p>
              </div>
            </div>
          ))}
        </div>
        {timeline.error ? <ErrorBanner body={timeline.error} /> : null}
        <div className="event-log">
          {model.recentEvents.map((event) => (
            <motion.div
              key={event.event_number}
              className="event-log__item"
              initial={reduceMotion ? undefined : { opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <div className="row row--between">
                <strong>{event.message}</strong>
                <span className="meta-line">#{event.event_number}</span>
              </div>
              <div className="meta-line">
                {event.display_status} | {event.display_stage} | {formatDateTime(event.ts)}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </Card>
  );
}
