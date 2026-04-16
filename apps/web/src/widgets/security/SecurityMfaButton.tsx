import type { ButtonHTMLAttributes, PropsWithChildren } from "react";

import { cn } from "../../shared/lib/cn";

type SecurityMfaButtonProps = PropsWithChildren<
  ButtonHTMLAttributes<HTMLButtonElement> & {
    fullWidth?: boolean;
    loading?: boolean;
    size?: "md" | "sm";
    variant?: "primary" | "secondary" | "danger";
  }
>;

export function SecurityMfaButton({
  children,
  className,
  fullWidth = false,
  loading = false,
  size = "md",
  variant = "primary",
  ...props
}: SecurityMfaButtonProps) {
  return (
    <button
      className={cn(
        "security-mfa-button",
        `security-mfa-button--${variant}`,
        `security-mfa-button--${size}`,
        fullWidth && "security-mfa-button--full",
        className,
      )}
      disabled={props.disabled || loading}
      {...props}
    >
      {loading ? <span aria-hidden="true" className="security-mfa-button__spinner" /> : null}
      {children}
    </button>
  );
}
