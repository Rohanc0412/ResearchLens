import { SecurityMessageBanner } from "./SecurityMessageBanner";
import { SecurityMfaCard } from "./SecurityMfaCard";
import { useSecurityMfa } from "./useSecurityMfa";

export function SecurityMfaPanel() {
  const securityMfa = useSecurityMfa();

  return (
    <div className="security-mfa-page">
      <header className="security-mfa-page__header">
        <h1>Security</h1>
        <p>Manage multi-factor authentication for your account.</p>
      </header>

      {securityMfa.errorMessage ? (
        <SecurityMessageBanner message={securityMfa.errorMessage} variant="error" />
      ) : null}
      {securityMfa.successMessage ? (
        <SecurityMessageBanner message={securityMfa.successMessage} variant="success" />
      ) : null}

      <SecurityMfaCard
        copied={securityMfa.copied}
        disableCode={securityMfa.disableCode}
        enabled={securityMfa.enabled}
        enrollment={securityMfa.enrollment}
        isWorking={securityMfa.isWorking}
        onCopySecret={securityMfa.handleCopySecret}
        onDisableCodeChange={securityMfa.setDisableCode}
        onDisableSubmit={securityMfa.handleDisable}
        onStart={securityMfa.handleStart}
        onVerificationCodeChange={securityMfa.setVerificationCode}
        onVerifySubmit={securityMfa.handleVerify}
        pending={securityMfa.pending}
        statusLoading={securityMfa.statusLoading}
        verificationCode={securityMfa.verificationCode}
      />
    </div>
  );
}
