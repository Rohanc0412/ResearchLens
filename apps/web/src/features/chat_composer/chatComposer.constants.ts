export const DEFAULT_MODEL = "gpt-4o-mini";
export const CUSTOM_MODEL_VALUE = "__custom__";

export const MODEL_OPTIONS = [
  { value: "gpt-4o-mini", label: "GPT-4o Mini" },
  { value: "gpt-4o", label: "GPT-4o" },
  { value: "anthropic/claude-3.5-sonnet", label: "Claude 3.5 Sonnet" },
  { value: "anthropic/claude-3.5-haiku", label: "Claude 3.5 Haiku" },
  { value: "google/gemini-2.0-flash", label: "Gemini 2.0 Flash" },
  { value: "meta-llama/llama-3.3-70b-instruct", label: "Llama 3.3 70B" },
  { value: CUSTOM_MODEL_VALUE, label: "Custom..." },
] as const;

export const QUICK_ACTIONS = [
  "Add conclusion",
  "Add recommendations",
  "Summarize findings",
  "Add references",
] as const;
