import { Navigate, useLocation } from "react-router-dom";

import { useAuth } from "../../app/providers/AuthProvider";
import { LegacyAuthCredentialsForm } from "./LegacyAuthCredentialsForm";
import {
  LegacyLoginErrorBanner,
  LegacyLoginSuccessBanner,
} from "./LegacyLoginBanners";
import { LegacyLoginFormShell } from "./LegacyLoginShared";
import { LegacyMfaForm } from "./LegacyMfaForm";
import {
  LegacyForgotPasswordForm,
  LegacyResetPasswordForm,
} from "./LegacyRecoveryForms";
import { MODE_TITLES, type LoginMode, LegacyLoginFrame } from "./legacyLoginContent";
import { useLegacyLoginFlow } from "./useLegacyLoginFlow";

function getSubtitle(mode: LoginMode) {
  if (mode === "register") return "Get started for free";
  if (mode === "forgot") return "We'll email you a reset code";
  if (mode === "reset") return "Enter your reset code and choose a new password";
  return "Sign in to your workspace";
}

export function LoginPage() {
  const auth = useAuth();
  const location = useLocation();
  const next =
    (location.state as { next?: string; from?: string } | null)?.next ??
    (location.state as { next?: string; from?: string } | null)?.from ??
    "/projects";
  const flow = useLegacyLoginFlow(auth);

  if (auth.status === "authenticated") {
    return <Navigate to={next} replace />;
  }

  return (
    <LegacyLoginFrame>
      <LegacyLoginFormShell
        title={MODE_TITLES[flow.activeKey]}
        subtitle={flow.showMfa ? undefined : getSubtitle(flow.mode)}
      >
        {flow.error ? <LegacyLoginErrorBanner message={flow.error} /> : null}
        {flow.success ? <LegacyLoginSuccessBanner message={flow.success} /> : null}

        {flow.showMfa ? (
          <LegacyMfaForm
            code={flow.mfaCode}
            isSubmitting={flow.isSubmitting}
            userLabel={flow.mfaUser}
            onCodeChange={(value) => {
              flow.clearFeedback();
              flow.setMfaCode(value);
            }}
            onStartOver={flow.cancelMfa}
            onSubmit={flow.submitMfa}
          />
        ) : flow.isForgot ? (
          <LegacyForgotPasswordForm
            email={flow.email}
            isSubmitting={flow.isSubmitting}
            onEmailChange={(value) => {
              flow.clearFeedback();
              flow.setEmail(value);
            }}
            onGoToLogin={() => flow.switchMode("login")}
            onGoToReset={() => flow.switchMode("reset")}
            onSubmit={flow.submitForgotPassword}
          />
        ) : flow.isReset ? (
          <LegacyResetPasswordForm
            isSubmitting={flow.isSubmitting}
            resetConfirm={flow.resetConfirm}
            resetPassword={flow.resetPassword}
            resetToken={flow.resetToken}
            onGoToForgot={() => flow.switchMode("forgot")}
            onGoToLogin={() => flow.switchMode("login")}
            onResetConfirmChange={(value) => {
              flow.clearFeedback();
              flow.setResetConfirm(value);
            }}
            onResetPasswordChange={(value) => {
              flow.clearFeedback();
              flow.setResetPassword(value);
            }}
            onResetTokenChange={(value) => {
              flow.clearFeedback();
              flow.setResetToken(value);
            }}
            onSubmit={flow.submitResetPassword}
          />
        ) : (
          <LegacyAuthCredentialsForm
            confirmPassword={flow.confirmPassword}
            email={flow.email}
            isRegister={flow.isRegister}
            isSubmitting={flow.isSubmitting}
            password={flow.password}
            username={flow.username}
            onConfirmPasswordChange={(value) => {
              flow.clearFeedback();
              flow.setConfirmPassword(value);
            }}
            onEmailChange={(value) => {
              flow.clearFeedback();
              flow.setEmail(value);
            }}
            onForgotPassword={() => flow.switchMode("forgot")}
            onPasswordChange={(value) => {
              flow.clearFeedback();
              flow.setPassword(value);
            }}
            onSubmit={flow.submitCredentials}
            onToggleMode={() => flow.switchMode(flow.isRegister ? "login" : "register")}
            onUsernameChange={(value) => {
              flow.clearFeedback();
              flow.setUsername(value);
            }}
          />
        )}
      </LegacyLoginFormShell>
    </LegacyLoginFrame>
  );
}
