export const DEFAULT_MODEL = "gpt-5-nano";
export const CUSTOM_MODEL_VALUE = "__custom__";

export const MODEL_OPTIONS = [
  { value: "gpt-5-nano", label: "GPT-5 Nano" },
  { value: CUSTOM_MODEL_VALUE, label: "Custom model" },
] as const;
