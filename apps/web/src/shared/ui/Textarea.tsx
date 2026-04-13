import type { TextareaHTMLAttributes } from "react";

import { cn } from "../lib/cn";

type TextareaProps = TextareaHTMLAttributes<HTMLTextAreaElement> & {
  label: string;
  hint?: string;
  error?: string;
};

export function Textarea({
  label,
  hint,
  error,
  className,
  rows = 6,
  ...props
}: TextareaProps) {
  return (
    <label className="field">
      <span className="field__label">{label}</span>
      <textarea className={cn("field__control", className)} rows={rows} {...props} />
      {error ? <span className="field__error">{error}</span> : null}
      {!error && hint ? <span className="field__help">{hint}</span> : null}
    </label>
  );
}
