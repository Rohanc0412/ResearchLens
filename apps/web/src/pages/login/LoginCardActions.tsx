import type { LoginMode } from "./authScreenContent";

export function LoginModeSwitch({
  mode,
  onModeChange,
}: {
  mode: LoginMode;
  onModeChange: (mode: LoginMode) => void;
}) {
  return (
    <div className="auth-mode-switch" role="tablist" aria-label="Authentication mode">
      <button
        type="button"
        role="tab"
        aria-selected={mode === "login"}
        className="auth-mode-switch__button"
        data-active={mode === "login"}
        onClick={() => onModeChange("login")}
      >
        Sign in
      </button>
      <button
        type="button"
        role="tab"
        aria-selected={mode === "register"}
        className="auth-mode-switch__button"
        data-active={mode === "register"}
        onClick={() => onModeChange("register")}
      >
        Create account
      </button>
    </div>
  );
}

export function LoginRecoveryActions({
  mode,
  onModeChange,
}: {
  mode: LoginMode;
  onModeChange: (mode: LoginMode) => void;
}) {
  return (
    <div className="auth-recovery">
      {mode === "login" ? (
        <button type="button" className="auth-inline-link" onClick={() => onModeChange("request_reset")}>
          Forgot password?
        </button>
      ) : mode === "register" ? (
        <button type="button" className="auth-inline-link" onClick={() => onModeChange("login")}>
          Already have an account?
        </button>
      ) : (
        <button type="button" className="auth-inline-link" onClick={() => onModeChange("request_reset")}>
          Need another reset token?
        </button>
      )}
      {mode === "request_reset" ? (
        <button type="button" className="auth-inline-link" onClick={() => onModeChange("confirm_reset")}>
          I already have a reset token
        </button>
      ) : null}
    </div>
  );
}
