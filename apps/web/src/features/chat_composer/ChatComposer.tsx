import type { KeyboardEvent } from "react";

import {
  CUSTOM_MODEL_VALUE,
  MODEL_OPTIONS,
  QUICK_ACTIONS,
} from "./chatComposer.constants";

type ChatComposerProps = {
  draft: string;
  isTyping: boolean;
  runPipelineArmed: boolean;
  selectedModel: string;
  customModel: string;
  onDraftChange: (value: string) => void;
  onSend: () => void;
  onQuickAction: (action: string) => void;
  onTogglePipeline: () => void;
  onModelChange: (value: string) => void;
  onCustomModelChange: (value: string) => void;
};

export function ChatComposer({
  draft,
  isTyping,
  runPipelineArmed,
  selectedModel,
  customModel,
  onDraftChange,
  onSend,
  onQuickAction,
  onTogglePipeline,
  onModelChange,
  onCustomModelChange,
}: ChatComposerProps) {
  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      onSend();
    }
  };

  return (
    <div className="chat-composer">
      <div className="chat-composer__quick-actions">
        {QUICK_ACTIONS.map((action) => (
          <button
            key={action}
            onClick={() => onQuickAction(action)}
            disabled={isTyping}
            className="chat-composer__quick-action"
          >
            {action}
          </button>
        ))}
      </div>

      <div className="chat-composer__controls">
        <div className="chat-composer__model-row">
          <span className="chat-composer__label">LLM model</span>
          <div className="chat-composer__model-fields">
            <select
              value={selectedModel}
              onChange={(event) => onModelChange(event.target.value)}
              aria-label="LLM model"
              className="chat-composer__select"
            >
              {MODEL_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            {selectedModel === CUSTOM_MODEL_VALUE ? (
              <input
                value={customModel}
                onChange={(event) => onCustomModelChange(event.target.value)}
                placeholder="Enter model id"
                aria-label="Custom model ID"
                className="chat-composer__input"
              />
            ) : null}
          </div>
          <button
            type="button"
            aria-pressed={runPipelineArmed}
            onClick={onTogglePipeline}
            className={`chat-composer__pipeline-toggle ${
              runPipelineArmed ? "chat-composer__pipeline-toggle--armed" : ""
            }`}
          >
            Run research report
          </button>
        </div>

        <div className="chat-composer__editor">
          <textarea
            value={draft}
            onChange={(event) => onDraftChange(event.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              runPipelineArmed
                ? "Describe your research topic - report will run on send..."
                : "Ask a question or request a report..."
            }
            aria-label="Message input"
            rows={3}
            className="chat-composer__textarea"
          />
          <button
            onClick={onSend}
            disabled={!draft.trim() || isTyping}
            aria-label="Send message"
            className={`chat-composer__send ${
              draft.trim() && !isTyping ? "chat-composer__send--active" : ""
            }`}
          >
            <svg viewBox="0 0 24 24" className="chat-composer__send-icon" aria-hidden="true">
              <path d="M3.4 20.4 22 12 3.4 3.6l.1 6.5L15 12 3.5 13.9l-.1 6.5Z" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
