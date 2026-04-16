import {
  LegacyFooterLinkRow,
  LegacyLoginButton,
  LegacyLoginField,
  LegacyStackedFooter,
} from "./LegacyLoginShared";

type LegacyForgotPasswordFormProps = {
  email: string;
  isSubmitting: boolean;
  onEmailChange: (value: string) => void;
  onGoToLogin: () => void;
  onGoToReset: () => void;
  onSubmit: () => void;
};

type LegacyResetPasswordFormProps = {
  isSubmitting: boolean;
  resetConfirm: string;
  resetPassword: string;
  resetToken: string;
  onGoToForgot: () => void;
  onGoToLogin: () => void;
  onResetConfirmChange: (value: string) => void;
  onResetPasswordChange: (value: string) => void;
  onResetTokenChange: (value: string) => void;
  onSubmit: () => void;
};

export function LegacyForgotPasswordForm({
  email,
  isSubmitting,
  onEmailChange,
  onGoToLogin,
  onGoToReset,
  onSubmit,
}: LegacyForgotPasswordFormProps) {
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
          id="forgot-email"
          autoComplete="email"
          label="Email"
          placeholder="you@company.com"
          required
          type="email"
          value={email}
          onChange={(event) => onEmailChange(event.target.value)}
        />

        <LegacyLoginButton loading={isSubmitting} type="submit">
          {isSubmitting ? "Requesting..." : "Send OTP"}
        </LegacyLoginButton>
      </form>

      <LegacyStackedFooter>
        <LegacyFooterLinkRow prompt="Remembered your password?" action="Back to sign in" onClick={onGoToLogin} />
        <LegacyFooterLinkRow prompt="Already have an OTP?" action="Enter OTP" onClick={onGoToReset} />
      </LegacyStackedFooter>
    </>
  );
}

export function LegacyResetPasswordForm({
  isSubmitting,
  resetConfirm,
  resetPassword,
  resetToken,
  onGoToForgot,
  onGoToLogin,
  onResetConfirmChange,
  onResetPasswordChange,
  onResetTokenChange,
  onSubmit,
}: LegacyResetPasswordFormProps) {
  return (
    <>
      <form
        className="legacy-login__stack"
        onSubmit={(event) => {
          event.preventDefault();
          void onSubmit();
        }}
      >
        {resetToken ? (
          <div className="legacy-login__dev-token">
            <p>OTP (local dev)</p>
            <code>{resetToken}</code>
          </div>
        ) : null}

        <LegacyLoginField
          id="reset-token"
          autoComplete="one-time-code"
          label="OTP code"
          placeholder="Enter OTP"
          required
          value={resetToken}
          onChange={(event) => onResetTokenChange(event.target.value)}
        />

        <LegacyLoginField
          id="reset-password"
          autoComplete="new-password"
          hint="Minimum 8 characters"
          label="New password"
          placeholder="Enter new password"
          required
          type="password"
          value={resetPassword}
          onChange={(event) => onResetPasswordChange(event.target.value)}
        />

        <LegacyLoginField
          id="reset-confirm"
          autoComplete="new-password"
          label="Confirm new password"
          placeholder="Re-enter new password"
          required
          type="password"
          value={resetConfirm}
          onChange={(event) => onResetConfirmChange(event.target.value)}
        />

        <LegacyLoginButton loading={isSubmitting} type="submit">
          {isSubmitting ? "Updating..." : "Reset password"}
        </LegacyLoginButton>
      </form>

      <LegacyStackedFooter>
        <LegacyFooterLinkRow prompt="Back to sign in?" action="Sign in" onClick={onGoToLogin} />
        <LegacyFooterLinkRow prompt="Need a new OTP?" action="Send again" onClick={onGoToForgot} />
      </LegacyStackedFooter>
    </>
  );
}
