import type { FormEventHandler } from "react";

import type { MfaEnrollStartResponseDto } from "@researchlens/api-client";

import { SecurityMfaDisableSection } from "./SecurityMfaDisableSection";
import { SecurityMfaEnrollmentSection } from "./SecurityMfaEnrollmentSection";
import { SecurityMfaButton } from "./SecurityMfaButton";
import { ShieldCheckIcon, ShieldOffIcon } from "./SecurityMfaIcons";

type SecurityMfaCardProps = {
  copied: boolean;
  disableCode: string;
  enabled: boolean;
  enrollment: MfaEnrollStartResponseDto | null;
  isWorking: boolean;
  onCopySecret: (secret: string) => Promise<void>;
  onDisableCodeChange: (value: string) => void;
  onDisableSubmit: FormEventHandler<HTMLFormElement>;
  onStart: () => Promise<void>;
  onVerificationCodeChange: (value: string) => void;
  onVerifySubmit: FormEventHandler<HTMLFormElement>;
  pending: boolean;
  statusLoading: boolean;
  verificationCode: string;
};

export function SecurityMfaCard({
  copied,
  disableCode,
  enabled,
  enrollment,
  isWorking,
  onCopySecret,
  onDisableCodeChange,
  onDisableSubmit,
  onStart,
  onVerificationCodeChange,
  onVerifySubmit,
  pending,
  statusLoading,
  verificationCode,
}: SecurityMfaCardProps) {
  return (
    <section className="security-mfa-card">
      <div className="security-mfa-card__header">
        <div className="security-mfa-card__identity">
          <span className="security-mfa-card__icon" aria-hidden="true">
            {enabled ? <ShieldCheckIcon /> : <ShieldOffIcon />}
          </span>
          <div>
            <div className="security-mfa-card__title">Authenticator app (TOTP)</div>
            <div className="security-mfa-status-label">
              <span className={`security-mfa-status-label__dot security-mfa-status-label__dot--${getState(enabled, pending)}`} />
              <span>{getStatusLabel(enabled, pending)}</span>
            </div>
          </div>
        </div>

        {!enabled ? (
          <SecurityMfaButton
            disabled={isWorking || statusLoading}
            loading={isWorking && enrollment === null}
            onClick={() => void onStart()}
            size="sm"
            variant="secondary"
          >
            {pending ? "Restart setup" : "Enable MFA"}
          </SecurityMfaButton>
        ) : null}
      </div>

      {enrollment ? (
        <SecurityMfaEnrollmentSection
          copied={copied}
          enrollment={enrollment}
          isWorking={isWorking}
          onCopySecret={onCopySecret}
          onVerificationCodeChange={onVerificationCodeChange}
          onVerifySubmit={onVerifySubmit}
          verificationCode={verificationCode}
        />
      ) : null}

      {enabled ? (
        <SecurityMfaDisableSection
          disableCode={disableCode}
          isWorking={isWorking}
          onDisableCodeChange={onDisableCodeChange}
          onDisableSubmit={onDisableSubmit}
        />
      ) : null}
    </section>
  );
}

function getStatusLabel(enabled: boolean, pending: boolean) {
  if (enabled) {
    return "Enabled";
  }
  return pending ? "Setup in progress" : "Not enabled";
}

function getState(enabled: boolean, pending: boolean) {
  if (enabled) {
    return "enabled";
  }
  return pending ? "pending" : "disabled";
}
