const dateTimeFormatter = new Intl.DateTimeFormat(undefined, {
  dateStyle: "medium",
  timeStyle: "short",
});

export function formatDateTime(value: string | null | undefined) {
  if (!value) {
    return "Unavailable";
  }

  return dateTimeFormatter.format(new Date(value));
}

export function titleFromPrompt(value: string) {
  const trimmed = value.trim();
  if (!trimmed) {
    return "Untitled conversation";
  }
  return trimmed.length > 64 ? `${trimmed.slice(0, 61)}...` : trimmed;
}
