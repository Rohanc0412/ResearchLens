import type { InputHTMLAttributes, ReactNode } from "react";

import { cn } from "../lib/cn";

type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  hint?: string;
  error?: string;
  controlAction?: ReactNode;
  inputClassName?: string;
};

export function Input({
  label,
  hint,
  error,
  className,
  controlAction,
  inputClassName,
  ...props
}: InputProps) {
  return (
    <label className="field">
      <span className="field__label">{label}</span>
      <span className={cn("field__control-wrap", className)}>
        <input className={cn("field__control", inputClassName)} {...props} />
        {controlAction ? <span className="field__control-action">{controlAction}</span> : null}
      </span>
      {error ? <span className="field__error">{error}</span> : null}
      {!error && hint ? <span className="field__help">{hint}</span> : null}
    </label>
  );
}
