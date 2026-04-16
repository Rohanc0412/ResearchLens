import { AnimatePresence, motion } from "framer-motion";
import type { ChangeEventHandler } from "react";

import { Button } from "../../shared/ui/Button";
import { ErrorBanner } from "../../shared/ui/ErrorBanner";
import {
  AuthStepRail,
  type AuthStepId,
  type AuthViewCopy,
  type LoginMode,
} from "./authScreenContent";
import { LoginModeSwitch, LoginRecoveryActions } from "./LoginCardActions";
import { LoginFieldSection } from "./LoginFieldSection";
import type { LoginFieldErrors } from "./loginFlowState";
import type { PasswordRequirement } from "./passwordPolicy";

type LoginWorkspaceCardProps = {
  activeStep: AuthStepId;
  authChallengeIdentifier?: string | null;
  authUserEmail?: string | null;
  canSubmit: boolean;
  currentView: AuthViewCopy;
  email: string;
  error: string | null;
  expirationReason: "expired" | "logout" | null;
  fieldErrors: LoginFieldErrors;
  identifier: string;
  isMfaChallenge: boolean;
  isPasswordResetMode: boolean;
  isSubmitting: boolean;
  mfaCode: string;
  mode: LoginMode;
  next: string;
  password: string;
  passwordGuidanceVisible: boolean;
  passwordRequirements: PasswordRequirement[];
  resetToken: string;
  shouldReduceMotion: boolean;
  showPassword: boolean;
  statusMessage: string | null;
  username: string;
  onEmailChange: ChangeEventHandler<HTMLInputElement>;
  onIdentifierChange: ChangeEventHandler<HTMLInputElement>;
  onMfaCodeChange: ChangeEventHandler<HTMLInputElement>;
  onModeChange: (mode: LoginMode) => void;
  onPasswordChange: ChangeEventHandler<HTMLInputElement>;
  onResetTokenChange: ChangeEventHandler<HTMLInputElement>;
  onResetToLogin: () => void;
  onStartOver: () => void;
  onSubmit: () => void;
  onTogglePassword: () => void;
  onUsernameChange: ChangeEventHandler<HTMLInputElement>;
};

export function LoginWorkspaceCard(props: LoginWorkspaceCardProps) {
  const {
    activeStep,
    authChallengeIdentifier,
    authUserEmail,
    canSubmit,
    currentView,
    email,
    error,
    expirationReason,
    fieldErrors,
    identifier,
    isMfaChallenge,
    isPasswordResetMode,
    isSubmitting,
    mfaCode,
    mode,
    next,
    password,
    passwordGuidanceVisible,
    passwordRequirements,
    resetToken,
    shouldReduceMotion,
    showPassword,
    statusMessage,
    username,
    onEmailChange,
    onIdentifierChange,
    onMfaCodeChange,
    onModeChange,
    onPasswordChange,
    onResetTokenChange,
    onResetToLogin,
    onStartOver,
    onSubmit,
    onTogglePassword,
    onUsernameChange,
  } = props;

  return (
    <motion.form
      className="auth-card"
      initial={shouldReduceMotion ? false : { opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={shouldReduceMotion ? { duration: 0 } : { duration: 0.26, ease: "easeOut" }}
      onSubmit={(event) => {
        event.preventDefault();
        void onSubmit();
      }}
    >
      <div className="auth-card__topbar">
        <div className="auth-context">
          <span className="auth-card__eyebrow">Authentication flow</span>
          <strong>
            {next === "/projects" ? "Default destination: projects workspace" : `Continue to ${next}`}
          </strong>
        </div>
        {isMfaChallenge ? (
          <button type="button" className="auth-inline-link" onClick={onStartOver}>
            Start over
          </button>
        ) : mode === "request_reset" || mode === "confirm_reset" ? (
          <button type="button" className="auth-inline-link" onClick={onResetToLogin}>
            Back to sign in
          </button>
        ) : null}
      </div>

      <AuthStepRail activeStep={activeStep} />
      {!isMfaChallenge ? <LoginModeSwitch mode={mode} onModeChange={onModeChange} /> : null}

      <div className="auth-card__heading">
        <span className="auth-card__eyebrow">{currentView.eyebrow}</span>
        <h2>{currentView.title}</h2>
        <p>{currentView.body}</p>
      </div>

      <div className="auth-security-row" aria-label="Session safeguards">
        {currentView.badges.map((badge) => (
          <span key={badge} className="pill auth-pill">
            {badge}
          </span>
        ))}
      </div>

      <div className="auth-form-stack">
        {expirationReason === "expired" ? (
          <ErrorBanner
            title="Session expired"
            body="Your session could not be restored. Sign in again to continue."
          />
        ) : null}
        {error ? <ErrorBanner body={error} /> : null}
        {statusMessage ? (
          <div className="status-banner" role="status" aria-live="polite">
            {statusMessage}
          </div>
        ) : null}

        <AnimatePresence mode="wait">
          <motion.div
            key={isMfaChallenge ? "mfa_challenge" : mode}
            className="auth-card__section"
            initial={shouldReduceMotion ? false : { opacity: 0, x: 12 }}
            animate={{ opacity: 1, x: 0 }}
            exit={shouldReduceMotion ? undefined : { opacity: 0, x: -12 }}
            transition={shouldReduceMotion ? { duration: 0 } : { duration: 0.18, ease: "easeOut" }}
          >
            <LoginFieldSection
              authChallengeIdentifier={authChallengeIdentifier}
              authUserEmail={authUserEmail}
              email={email}
              fieldErrors={fieldErrors}
              identifier={identifier}
              isMfaChallenge={isMfaChallenge}
              isPasswordResetMode={isPasswordResetMode}
              mfaCode={mfaCode}
              mode={mode}
              password={password}
              passwordGuidanceVisible={passwordGuidanceVisible}
              passwordRequirements={passwordRequirements}
              resetToken={resetToken}
              showPassword={showPassword}
              username={username}
              onEmailChange={onEmailChange}
              onIdentifierChange={onIdentifierChange}
              onMfaCodeChange={onMfaCodeChange}
              onPasswordChange={onPasswordChange}
              onResetTokenChange={onResetTokenChange}
              onTogglePassword={onTogglePassword}
              onUsernameChange={onUsernameChange}
            />
          </motion.div>
        </AnimatePresence>

        <Button variant="primary" type="submit" loading={isSubmitting} disabled={!canSubmit}>
          {currentView.primaryLabel}
        </Button>

        {isMfaChallenge ? null : <LoginRecoveryActions mode={mode} onModeChange={onModeChange} />}
      </div>

      <div className="auth-support-card">
        <strong>{currentView.supportTitle}</strong>
        <p>{currentView.supportBody}</p>
      </div>

      <p className="auth-card__footer-note">{currentView.footer}</p>
    </motion.form>
  );
}
