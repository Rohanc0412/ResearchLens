import { AuthService } from "@researchlens/api-client";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { useAuth } from "../../app/providers/AuthProvider";
import { getErrorMessage } from "../../shared/api/errors";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";
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

  return (
    <div className="auth-shell">
      <Card className="auth-card" title="ResearchLens" meta="Obsidian session access">
        <div className="stack">
          <div className="segmented">
            {[
              ["login", "Login"],
              ["register", "Register"],
              ["request_reset", "Reset request"],
              ["confirm_reset", "Reset confirm"],
            ].map(([value, label]) => (
              <button
                key={value}
                className="segmented__item"
                data-active={mode === value}
                onClick={() => setMode(value as LoginMode)}
                type="button"
              >
                {label}
              </button>
            ))}
          </div>

          {auth.expirationReason === "expired" ? (
            <ErrorBanner body="Your session expired. Sign in again or let the refresh cookie restore access." />
          ) : null}
          {error ? <ErrorBanner body={error} /> : null}
          {statusMessage ? <Card title="Status">{statusMessage}</Card> : null}

          {auth.status === "mfa_challenge" ? (
            <>
              <Input
                label="MFA code"
                value={mfaCode}
                onChange={(event) => setMfaCode(event.target.value)}
              />
              <Button variant="primary" onClick={() => void handlePrimary()}>
                Verify challenge
              </Button>
            </>
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
                  value={identifier}
                  onChange={(event) => setIdentifier(event.target.value)}
                />
              ) : null}
              {mode !== "request_reset" ? (
                <Input
                  label="Password"
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                />
              ) : null}
              <Button variant="primary" onClick={() => void handlePrimary()}>
                {mode === "register"
                  ? "Create account"
                  : mode === "request_reset"
                    ? "Send reset link"
                    : mode === "confirm_reset"
                      ? "Confirm reset"
                      : "Sign in"}
              </Button>
            </>
          )}
        </div>
      </Card>
    </div>
  );
}
