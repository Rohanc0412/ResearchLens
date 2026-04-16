import { AuthService } from "@researchlens/api-client";
import { useEffect, useMemo, useState } from "react";

import { getErrorMessage } from "../../shared/api/errors";
import type { LoginMode } from "./legacyLoginContent";
import { SIGNUP_SUCCESS_KEY } from "./LegacyLoginShared";

type LegacyAuthAdapter = {
  challenge: { identifier: string } | null;
  clearExpirationReason: () => void;
  clearSession: () => void;
  expirationReason: "expired" | "logout" | null;
  login: (payload: { identifier: string; password: string }) => Promise<"authenticated" | "mfa_required">;
  status: "bootstrapping" | "anonymous" | "authenticated" | "mfa_challenge";
  user: { email: string; username: string } | null;
  verifyMfaChallenge: (code: string) => Promise<void>;
};

function readSignupMessage() {
  try {
    const message = window.sessionStorage.getItem(SIGNUP_SUCCESS_KEY);
    if (message) {
      window.sessionStorage.removeItem(SIGNUP_SUCCESS_KEY);
    }
    return message;
  } catch {
    return null;
  }
}

function writeSignupMessage(message: string) {
  try {
    window.sessionStorage.setItem(SIGNUP_SUCCESS_KEY, message);
  } catch {
    // Storage access is optional for this transient banner.
  }
}

function readResetToken(response: unknown) {
  const candidate = response as { reset_token?: unknown };
  return typeof candidate.reset_token === "string" ? candidate.reset_token : "";
}

export function useLegacyLoginFlow(auth: LegacyAuthAdapter) {
  const [mode, setMode] = useState<LoginMode>("login");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [mfaCode, setMfaCode] = useState("");
  const [resetToken, setResetToken] = useState("");
  const [resetPassword, setResetPassword] = useState("");
  const [resetConfirm, setResetConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const showMfa = auth.status === "mfa_challenge";
  const isRegister = mode === "register";
  const isForgot = mode === "forgot";
  const isReset = mode === "reset";
  const activeKey = showMfa ? "mfa" : mode;
  const mfaUser = useMemo(
    () => (auth.challenge?.identifier ?? auth.user?.email ?? auth.user?.username ?? username) || null,
    [auth.challenge?.identifier, auth.user?.email, auth.user?.username, username],
  );

  useEffect(() => {
    const message = readSignupMessage();
    if (message) {
      setSuccess(message);
    }
  }, []);

  function clearFeedback() {
    setError(null);
    setSuccess(null);
    auth.clearExpirationReason();
  }

  function switchMode(nextMode: LoginMode) {
    clearFeedback();
    setIsSubmitting(false);
    setEmail("");
    setPassword("");
    setConfirmPassword("");
    setUsername("");
    setResetPassword("");
    setResetConfirm("");
    setMode(nextMode);
  }

  async function submitCredentials() {
    clearFeedback();
    if (!username.trim()) {
      setError("Username is required.");
      return;
    }
    if (!password.trim()) {
      setError("Password is required.");
      return;
    }

    setIsSubmitting(true);
    try {
      if (isRegister) {
        if (password.length < 8) throw new Error("Password must be at least 8 characters.");
        if (password !== confirmPassword) throw new Error("Passwords do not match.");
        await AuthService.registerAuthRegisterPost({ username: username.trim(), email: email.trim(), password });
        writeSignupMessage("Account created successfully! You can now sign in.");
        await AuthService.logoutAuthLogoutPost().catch(() => undefined);
        auth.clearSession();
        setMode("login");
        setEmail("");
        setPassword("");
        setConfirmPassword("");
        setSuccess("Account created successfully! You can now sign in.");
        return;
      }

      const result = await auth.login({ identifier: username.trim(), password });
      if (result === "mfa_required") {
        setMfaCode("");
      }
    } catch (err) {
      const fallback = isRegister ? "Sign up failed. Try again." : "Login failed. Try again.";
      setError(getErrorMessage(err) ?? fallback);
    } finally {
      setIsSubmitting(false);
    }
  }

  async function submitForgotPassword() {
    clearFeedback();
    setIsSubmitting(true);
    try {
      const response = await AuthService.requestPasswordResetAuthPasswordResetRequestPost({
        email: email.trim(),
      });
      const token = readResetToken(response);
      setResetToken(token);
      setResetPassword("");
      setResetConfirm("");
      setMode("reset");
      setSuccess(
        token
          ? "Reset token generated. Enter a new password to continue."
          : "If the account exists, an OTP was generated. Enter it below to reset your password.",
      );
    } catch (err) {
      setError(getErrorMessage(err) ?? "Password reset request failed.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function submitResetPassword() {
    clearFeedback();
    setIsSubmitting(true);
    try {
      if (resetPassword.length < 8) throw new Error("Password must be at least 8 characters.");
      if (resetPassword !== resetConfirm) throw new Error("Passwords do not match.");
      await AuthService.confirmPasswordResetAuthPasswordResetConfirmPost({
        token: resetToken.trim(),
        password: resetPassword,
      });
      setSuccess("Password updated. Please sign in.");
      setResetPassword("");
      setResetConfirm("");
      setResetToken("");
      setMode("login");
    } catch (err) {
      setError(getErrorMessage(err) ?? "Password reset failed.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function submitMfa() {
    if (!showMfa) return;
    clearFeedback();
    setIsSubmitting(true);
    try {
      await auth.verifyMfaChallenge(mfaCode.trim());
    } catch (err) {
      setError(getErrorMessage(err) ?? "MFA verification failed.");
    } finally {
      setIsSubmitting(false);
    }
  }

  function cancelMfa() {
    auth.clearSession();
    setMfaCode("");
    setUsername("");
    setMode("login");
    clearFeedback();
  }

  return {
    activeKey,
    cancelMfa,
    clearFeedback,
    confirmPassword,
    email,
    error,
    isForgot,
    isRegister,
    isReset,
    isSubmitting,
    mfaCode,
    mfaUser,
    mode,
    password,
    resetConfirm,
    resetPassword,
    resetToken,
    setConfirmPassword,
    setEmail,
    setMfaCode,
    setPassword,
    setResetConfirm,
    setResetPassword,
    setResetToken,
    setUsername,
    showMfa,
    submitCredentials,
    submitForgotPassword,
    submitMfa,
    submitResetPassword,
    success,
    switchMode,
    username,
  };
}
