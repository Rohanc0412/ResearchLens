import type { InputHTMLAttributes, PropsWithChildren, ReactNode } from "react";

export const SIGNUP_SUCCESS_KEY = "researchops_signup_success";
export const PASSWORD_MASK = "\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022";

type LegacyLoginFieldProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  hint?: string;
};

type LegacyLoginButtonProps = PropsWithChildren<{
  disabled?: boolean;
  loading?: boolean;
  variant?: "primary" | "secondary";
  type?: "button" | "submit";
  onClick?: () => void;
}>;

type FooterRowProps = {
  prompt: string;
  action: string;
  onClick: () => void;
};

export function LegacyLoginField({ label, hint, id, ...props }: LegacyLoginFieldProps) {
  return (
    <div className="legacy-login__field-group">
      <label htmlFor={id}>{label}</label>
      <input id={id} {...props} />
      {hint ? <p className="legacy-login__hint">{hint}</p> : null}
    </div>
  );
}

export function LegacyLoginButton({
  children,
  disabled,
  loading = false,
  onClick,
  type = "button",
  variant = "primary",
}: LegacyLoginButtonProps) {
  return (
    <button
      type={type}
      className={`legacy-login__button legacy-login__button--${variant}`}
      disabled={disabled || loading}
      onClick={onClick}
    >
      {loading ? <span className="legacy-login__spinner" aria-hidden="true" /> : null}
      {children}
    </button>
  );
}

export function LegacyLoginFormShell({
  children,
  title,
  subtitle,
}: PropsWithChildren<{ title: string; subtitle?: string }>) {
  return (
    <section className="legacy-login__card">
      <header className="legacy-login__header">
        <h1>{title}</h1>
        {subtitle ? <p>{subtitle}</p> : null}
      </header>
      {children}
    </section>
  );
}

export function LegacyFooterLinkRow({ prompt, action, onClick }: FooterRowProps) {
  return (
    <div className="legacy-login__footer-row">
      <span>{prompt}</span>
      <button type="button" onClick={onClick}>
        {action}
      </button>
    </div>
  );
}

export function LegacyStackedFooter({ children }: PropsWithChildren) {
  return <div className="legacy-login__footer-links legacy-login__footer-links--stacked">{children}</div>;
}

export function LegacyInlineLink({
  children,
  onClick,
}: PropsWithChildren<{ onClick: () => void }>) {
  return (
    <button type="button" onClick={onClick}>
      {children}
    </button>
  );
}

export function LegacyMfaPanel({ children }: { children: ReactNode }) {
  return <div className="legacy-login__mfa-panel">{children}</div>;
}
