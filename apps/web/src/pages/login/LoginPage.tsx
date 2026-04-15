import { AuthService } from "@researchlens/api-client";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { useAuth } from "../../app/providers/AuthProvider";
import { getErrorMessage } from "../../shared/api/errors";
import { Button } from "../../shared/ui/Button";
import { ErrorBanner } from "../../shared/ui/ErrorBanner";
import { Input } from "../../shared/ui/Input";

type LoginMode = "login" | "register" | "request_reset" | "confirm_reset";

export function LoginPage() {
  const auth = useAuth();
  const location = useLocation();
  const [mode, setMode] = useState<LoginMode>("login");
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [resetToken, setResetToken] = useState("");
  const [mfaCode, setMfaCode] = useState("");
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const next = (location.state as { next?: string } | null)?.next ?? "/projects";

  const requestReset = useMutation({
    mutationFn: (payload: { email: string }) =>
      AuthService.requestPasswordResetAuthPasswordResetRequestPost(payload),
  });
  const confirmReset = useMutation({
    mutationFn: (payload: { token: string; password: string }) =>
      AuthService.confirmPasswordResetAuthPasswordResetConfirmPost(payload),
  });

  if (auth.status === "authenticated") {
    return <Navigate to={next} replace />;
  }

  const handlePrimary = async () => {
    try {
      setError(null);
      setStatusMessage(null);
      if (auth.status === "mfa_challenge") {
        await auth.verifyMfaChallenge(mfaCode);
        return;
      }

      if (mode === "register") {
        await auth.register({ username, email, password });
        return;
      }

      if (mode === "request_reset") {
        await requestReset.mutateAsync({ email });
        setStatusMessage("Password reset request accepted. Check the configured mail sink.");
        return;
      }

      if (mode === "confirm_reset") {
        await confirmReset.mutateAsync({ token: resetToken, password });
        setStatusMessage("Password updated. You can log in now.");
        setMode("login");
        return;
      }

      await auth.login({ identifier, password });
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const primaryLabel =
    mode === "register"
      ? "Create account"
      : mode === "request_reset"
        ? "Send reset link"
        : mode === "confirm_reset"
          ? "Confirm reset"
          : "Sign in";

  return (
    <div className="auth-shell">
      <aside className="auth-panel" aria-label="ResearchLens overview">
        <div className="auth-brand">
          <span className="auth-brand__mark" aria-hidden="true">
            <svg viewBox="0 0 24 24" role="img">
              <path d="M12 3.25 5.75 5.6v4.95c0 4.05 2.55 7.75 6.25 9.15 3.7-1.4 6.25-5.1 6.25-9.15V5.6L12 3.25Z" />
            </svg>
          </span>
          <span>ResearchLens</span>
        </div>

        <div className="auth-copy">
          <h1>Research, organised. Insights, amplified.</h1>
          <p>
            The AI-powered workspace for ResearchLens teams. Run sessions,
            synthesise evidence, and surface what matters.
          </p>
        </div>

        <ul className="auth-benefits" aria-label="ResearchLens capabilities">
          <li>
            <span aria-hidden="true">
              <svg viewBox="0 0 24 24">
                <path d="M9 3 5.5 10.2 9 21M15 3l3.5 7.2L15 21M4 15l16-6" />
              </svg>
            </span>
            AI-powered research synthesis
          </li>
          <li>
            <span aria-hidden="true">
              <svg viewBox="0 0 24 24">
                <path d="m12 3 1.55 5.45L19 10l-5.45 1.55L12 17l-1.55-5.45L5 10l5.45-1.55L12 3ZM18 16l.7 2.3L21 19l-2.3.7L18 22l-.7-2.3L15 19l2.3-.7L18 16Z" />
              </svg>
            </span>
            Evidence management &amp; tagging
          </li>
          <li>
            <span aria-hidden="true">
              <svg viewBox="0 0 24 24">
                <path d="m13 2-8 12h6l-1 8 9-13h-6l0-7Z" />
              </svg>
            </span>
            Fast, secure, team-ready
          </li>
        </ul>

        <p className="auth-copyright">&copy; 2026 ResearchLens</p>
      </aside>

      <main className="auth-workspace">
        <form
          className="auth-card"
          onSubmit={(event) => {
            event.preventDefault();
            void handlePrimary();
          }}
        >
          <div className="auth-card__heading">
            <h2>
              {auth.status === "mfa_challenge"
                ? "Verify access"
                : mode === "register"
                  ? "Create workspace"
                  : mode === "request_reset"
                    ? "Reset password"
                    : mode === "confirm_reset"
                      ? "Set new password"
                      : "Welcome back"}
            </h2>
            <p>
              {auth.status === "mfa_challenge"
                ? "Enter your multi-factor code"
                : mode === "register"
                  ? "Start your ResearchLens workspace"
                  : mode === "request_reset"
                    ? "Request a password reset token"
                    : mode === "confirm_reset"
                      ? "Use your reset token"
                      : "Sign in to your workspace"}
            </p>
          </div>

          <div className="auth-form-stack">
            {auth.expirationReason === "expired" ? (
              <ErrorBanner body="Your session expired. Sign in again or let the refresh cookie restore access." />
            ) : null}
            {error ? <ErrorBanner body={error} /> : null}
            {statusMessage ? <div className="auth-status">{statusMessage}</div> : null}

            {auth.status === "mfa_challenge" ? (
              <Input
                label="MFA code"
                value={mfaCode}
                onChange={(event) => setMfaCode(event.target.value)}
              />
            ) : (
              <>
                {mode === "register" ? (
                  <Input
                    label="Username"
                    value={username}
                    onChange={(event) => setUsername(event.target.value)}
                  />
                ) : null}
                {mode === "register" || mode === "request_reset" ? (
                  <Input
                    label="Email"
                    type="email"
                    placeholder="you@company.com"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                  />
                ) : null}
                {mode === "confirm_reset" ? (
                  <Input
                    label="Reset token"
                    value={resetToken}
                    onChange={(event) => setResetToken(event.target.value)}
                  />
                ) : null}
                {mode === "login" ? (
                  <Input
                    label="Username or email"
                    placeholder="you@company.com"
                    value={identifier}
                    onChange={(event) => setIdentifier(event.target.value)}
                  />
                ) : null}
                {mode !== "request_reset" ? (
                  <Input
                    label="Password"
                    type="password"
                    placeholder="********"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                  />
                ) : null}
              </>
            )}

            <Button variant="primary" type="submit">
              {auth.status === "mfa_challenge" ? "Verify challenge" : primaryLabel}
            </Button>

            {auth.status === "mfa_challenge" ? null : (
              <div className="auth-link-row">
                {mode === "login" ? (
                  <button type="button" onClick={() => setMode("request_reset")}>
                    Forgot password?
                  </button>
                ) : (
                  <button type="button" onClick={() => setMode("login")}>
                    Back to sign in
                  </button>
                )}
                {mode === "request_reset" ? (
                  <button type="button" onClick={() => setMode("confirm_reset")}>
                    Have a reset token?
                  </button>
                ) : null}
              </div>
            )}
          </div>

          {auth.status === "mfa_challenge" ? null : (
            <div className="auth-card__footer">
              <span>
                {mode === "register"
                  ? "Already have a workspace?"
                  : "New to ResearchLens?"}
              </span>
              <button
                type="button"
                onClick={() => setMode(mode === "register" ? "login" : "register")}
              >
                {mode === "register" ? "Sign in" : "Create one"}
              </button>
            </div>
          )}
        </form>
      </main>
    </div>
  );
}
