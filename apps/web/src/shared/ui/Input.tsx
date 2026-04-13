import type { InputHTMLAttributes } from "react";

import { cn } from "../lib/cn";

type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  hint?: string;
  error?: string;
};

export function Input({ label, hint, error, className, ...props }: InputProps) {
  return (
    <label className="field">
      <span className="field__label">{label}</span>
      <input className={cn("field__control", className)} {...props} />
      {error ? <span className="field__error">{error}</span> : null}
      {!error && hint ? <span className="field__help">{hint}</span> : null}
    </label>
  );
}
