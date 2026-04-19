import { motion } from "framer-motion";

import type { ResearchProgressCardModel } from "./runProgress.types";

type ProgressEventLogProps = {
  expanded: boolean;
  currentAction: ResearchProgressCardModel["currentAction"];
  events: ResearchProgressCardModel["recentEvents"];
};

export function ProgressEventLog({ expanded, currentAction, events }: ProgressEventLogProps) {
  if (!expanded) return null;

  return (
    <div className="legacy-progress-log">
      <div className="legacy-progress-log__header">
        <span>Progress updates</span>
        <span>{currentAction ? events.length + 1 : events.length} events</span>
      </div>
      {!currentAction && events.length === 0 ? (
        <div className="legacy-progress-log__empty">
          Waiting for progress events from the run stream.
        </div>
      ) : (
        <div className="legacy-progress-log__list">
          {currentAction ? (
            <motion.div
              className="legacy-progress-log__item legacy-progress-log__item--active"
              animate={{ opacity: [1, 0.45, 1] }}
              transition={{ duration: 2, ease: "easeInOut", repeat: Infinity }}
            >
              <div className="legacy-progress-log__meta">
                <span>{currentAction.level}</span>
                <span>now</span>
              </div>
              <div className="legacy-progress-log__message">{currentAction.message}</div>
              {currentAction.detail ? (
                <div className="legacy-progress-log__detail">{currentAction.detail}</div>
              ) : null}
            </motion.div>
          ) : null}
          {events.map((event) => (
            <div key={event.id} className="legacy-progress-log__item">
              <div className="legacy-progress-log__meta">
                <span>{event.level}</span>
                <span>{new Date(event.ts).toLocaleTimeString()}</span>
              </div>
              <div className="legacy-progress-log__message">{event.message}</div>
              {event.detail ? (
                <div className="legacy-progress-log__detail">{event.detail}</div>
              ) : null}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
