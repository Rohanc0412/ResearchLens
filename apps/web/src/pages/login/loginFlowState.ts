import type { AuthStepId, LoginMode } from "./authScreenContent";

export type LoginFieldErrors = {
  username?: string;
  email?: string;
  identifier?: string;
  password?: string;
  resetToken?: string;
  mfaCode?: string;
};

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function isEmailAddress(value: string) {
  return EMAIL_PATTERN.test(value.trim());
}

export function getActiveStep(mode: LoginMode, isMfaChallenge: boolean): AuthStepId {
  if (isMfaChallenge) {
    return "verification";
  }
  if (mode === "request_reset" || mode === "confirm_reset") {
    return "recovery";
  }
  return "access";
}

export function getCanSubmit({
  email,
  identifier,
  isMfaChallenge,
  mfaCode,
  mode,
  password,
  passwordError,
  resetToken,
  username,
}: {
  email: string;
  identifier: string;
  isMfaChallenge: boolean;
  mfaCode: string;
  mode: LoginMode;
  password: string;
  passwordError: string | undefined;
  resetToken: string;
  username: string;
}) {
  if (isMfaChallenge) {
    return /^\d{6}$/.test(mfaCode.trim());
  }
  if (mode === "register") {
    return Boolean(username.trim()) && isEmailAddress(email) && !passwordError;
  }
  if (mode === "request_reset") {
    return isEmailAddress(email);
  }
  if (mode === "confirm_reset") {
    return Boolean(resetToken.trim()) && !passwordError;
  }
  return Boolean(identifier.trim()) && Boolean(password);
}

export function getFieldErrors({
  email,
  identifier,
  isMfaChallenge,
  isRegisterMode,
  mode,
  mfaCode,
  password,
  passwordError,
  passwordGuidanceVisible,
  resetToken,
  submitted,
  username,
}: {
  email: string;
  identifier: string;
  isMfaChallenge: boolean;
  isRegisterMode: boolean;
  mode: LoginMode;
  mfaCode: string;
  password: string;
  passwordError: string | undefined;
  passwordGuidanceVisible: boolean;
  resetToken: string;
  submitted: boolean;
  username: string;
}): LoginFieldErrors {
  return {
    username: submitted && isRegisterMode && !username.trim() ? "Enter a username." : undefined,
    email:
      submitted && (isRegisterMode || mode === "request_reset") && !email.trim()
        ? "Enter your email address."
        : submitted && (isRegisterMode || mode === "request_reset") && !isEmailAddress(email)
          ? "Enter a valid email address."
          : undefined,
    identifier:
      submitted && mode === "login" && !identifier.trim()
        ? "Enter your username or email."
        : undefined,
    password:
      submitted && mode === "login" && !password
        ? "Enter your password."
        : submitted && passwordGuidanceVisible
          ? passwordError
          : undefined,
    resetToken:
      submitted && mode === "confirm_reset" && !resetToken.trim()
        ? "Enter the reset token."
        : undefined,
    mfaCode:
      submitted && isMfaChallenge && !/^\d{6}$/.test(mfaCode.trim())
        ? "Enter the 6-digit code from your authenticator app."
        : undefined,
  };
}
