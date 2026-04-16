import type { ChangeEventHandler } from "react";

import { Input } from "../../shared/ui/Input";
import type { LoginMode } from "./authScreenContent";
import type { LoginFieldErrors } from "./loginFlowState";
import { PasswordChecklist } from "./PasswordChecklist";
import type { PasswordRequirement } from "./passwordPolicy";

type LoginFieldSectionProps = {
  authChallengeIdentifier?: string | null;
  authUserEmail?: string | null;
  email: string;
  fieldErrors: LoginFieldErrors;
  identifier: string;
  isMfaChallenge: boolean;
  isPasswordResetMode: boolean;
  mfaCode: string;
  mode: LoginMode;
  password: string;
  passwordGuidanceVisible: boolean;
  passwordRequirements: PasswordRequirement[];
  resetToken: string;
  showPassword: boolean;
  username: string;
  onEmailChange: ChangeEventHandler<HTMLInputElement>;
  onIdentifierChange: ChangeEventHandler<HTMLInputElement>;
  onMfaCodeChange: ChangeEventHandler<HTMLInputElement>;
  onPasswordChange: ChangeEventHandler<HTMLInputElement>;
  onResetTokenChange: ChangeEventHandler<HTMLInputElement>;
  onTogglePassword: () => void;
  onUsernameChange: ChangeEventHandler<HTMLInputElement>;
};

export function LoginFieldSection({
  authChallengeIdentifier,
  authUserEmail,
  email,
  fieldErrors,
  identifier,
  isMfaChallenge,
  isPasswordResetMode,
  mfaCode,
  mode,
  password,
  passwordGuidanceVisible,
  passwordRequirements,
  resetToken,
  showPassword,
  username,
  onEmailChange,
  onIdentifierChange,
  onMfaCodeChange,
  onPasswordChange,
  onResetTokenChange,
  onTogglePassword,
  onUsernameChange,
}: LoginFieldSectionProps) {
  if (isMfaChallenge) {
    return (
      <>
        <Input
          label="Authenticator code"
          placeholder="123456"
          inputMode="numeric"
          autoComplete="one-time-code"
          maxLength={6}
          value={mfaCode}
          error={fieldErrors.mfaCode}
          onChange={onMfaCodeChange}
        />
        <div className="auth-support-card auth-support-card--compact">
          <strong>Pending sign-in</strong>
          <p>
            Challenge for{" "}
            <span className="auth-identity">
              {authChallengeIdentifier ?? authUserEmail ?? "your workspace"}
            </span>
          </p>
        </div>
      </>
    );
  }

  return (
    <>
      {mode === "register" ? (
        <Input
          label="Username"
          placeholder="analyst.team"
          autoComplete="username"
          autoCapitalize="none"
          spellCheck={false}
          value={username}
          error={fieldErrors.username}
          onChange={onUsernameChange}
        />
      ) : null}
      {mode === "register" || mode === "request_reset" ? (
        <Input
          label="Email"
          type="email"
          placeholder="you@company.com"
          autoComplete="email"
          autoCapitalize="none"
          spellCheck={false}
          value={email}
          error={fieldErrors.email}
          onChange={onEmailChange}
        />
      ) : null}
      {mode === "confirm_reset" ? (
        <Input
          label="Reset token"
          placeholder="Paste your reset token"
          autoComplete="one-time-code"
          value={resetToken}
          error={fieldErrors.resetToken}
          onChange={onResetTokenChange}
        />
      ) : null}
      {mode === "login" ? (
        <Input
          label="Username or email"
          placeholder="you@company.com"
          autoComplete="username"
          autoCapitalize="none"
          spellCheck={false}
          value={identifier}
          error={fieldErrors.identifier}
          onChange={onIdentifierChange}
        />
      ) : null}
      {mode !== "request_reset" ? (
        <Input
          label="Password"
          type={showPassword ? "text" : "password"}
          placeholder={mode === "login" ? "Enter your password" : "Create a strong password"}
          autoComplete={mode === "login" ? "current-password" : "new-password"}
          value={password}
          error={fieldErrors.password}
          onChange={onPasswordChange}
          controlAction={
            <button
              type="button"
              className="auth-password-toggle"
              onClick={onTogglePassword}
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? "Hide" : "Show"}
            </button>
          }
        />
      ) : null}
      {passwordGuidanceVisible ? (
        <PasswordChecklist
          requirements={passwordRequirements}
          identityReminder={
            isPasswordResetMode
              ? "Your new password must also not match your username or email."
              : undefined
          }
        />
      ) : null}
    </>
  );
}
