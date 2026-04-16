import { useState } from "react";

import { PasswordChecklist } from "./PasswordChecklist";
import { getPasswordRequirements } from "./passwordPolicy";
import {
  LegacyFooterLinkRow,
  LegacyInlineLink,
  LegacyLoginButton,
  LegacyLoginField,
} from "./LegacyLoginShared";

type LegacyAuthCredentialsFormProps = {
  confirmPassword: string;
  isRegister: boolean;
  isSubmitting: boolean;
  password: string;
  username: string;
  email: string;
  onConfirmPasswordChange: (value: string) => void;
  onEmailChange: (value: string) => void;
  onForgotPassword: () => void;
  onPasswordChange: (value: string) => void;
  onSubmit: () => void;
  onToggleMode: () => void;
  onUsernameChange: (value: string) => void;
};

export function LegacyAuthCredentialsForm({
  confirmPassword,
  email,
  isRegister,
  isSubmitting,
  password,
  username,
  onConfirmPasswordChange,
  onEmailChange,
  onForgotPassword,
  onPasswordChange,
  onSubmit,
  onToggleMode,
  onUsernameChange,
}: LegacyAuthCredentialsFormProps) {
  const [isPasswordFocused, setIsPasswordFocused] = useState(false);

  const passwordRequirements = isRegister
    ? getPasswordRequirements({ password, username, email, includeIdentityRules: true })
    : [];

  const showChecklist = isRegister && isPasswordFocused;

  return (
    <>
      <form
        className="legacy-login__stack"
        onSubmit={(event) => {
          event.preventDefault();
          void onSubmit();
        }}
      >
        <LegacyLoginField
          id="login-username"
          autoComplete="username"
          label="Username or email"
          placeholder="you@company.com"
          required
          value={username}
          onChange={(event) => onUsernameChange(event.target.value)}
        />

        {isRegister ? (
          <LegacyLoginField
            id="login-email"
            autoComplete="email"
            label="Email"
            placeholder="you@company.com"
            required
            type="email"
            value={email}
            onChange={(event) => onEmailChange(event.target.value)}
          />
        ) : null}

        <div className="legacy-login__field-wrapper">
          <LegacyLoginField
            id="login-password"
            autoComplete={isRegister ? "new-password" : "current-password"}
            label="Password"
            placeholder="Enter your password"
            required
            type="password"
            value={password}
            onChange={(event) => onPasswordChange(event.target.value)}
            onFocus={() => setIsPasswordFocused(true)}
            onBlur={() => setIsPasswordFocused(false)}
          />
          {showChecklist ? (
            <PasswordChecklist
              className="password-checklist--popup"
              requirements={passwordRequirements}
            />
          ) : null}
        </div>

        {isRegister ? (
          <LegacyLoginField
            id="login-confirm"
            autoComplete="new-password"
            label="Confirm password"
            placeholder="Re-enter your password"
            required
            type="password"
            value={confirmPassword}
            onChange={(event) => onConfirmPasswordChange(event.target.value)}
          />
        ) : null}

        <LegacyLoginButton loading={isSubmitting} type="submit">
          {isSubmitting ? (isRegister ? "Creating account..." : "Signing in...") : isRegister ? "Create account" : "Sign in"}
        </LegacyLoginButton>
      </form>

      {!isRegister ? (
        <div className="legacy-login__forgot-row">
          <LegacyInlineLink onClick={onForgotPassword}>Forgot password?</LegacyInlineLink>
        </div>
      ) : null}

      <div className="legacy-login__footer-links">
        <span>{isRegister ? "Already have an account?" : "New to ResearchOps Studio?"}</span>
        <LegacyInlineLink onClick={onToggleMode}>{isRegister ? "Sign in" : "Create one"}</LegacyInlineLink>
      </div>
    </>
  );
}
