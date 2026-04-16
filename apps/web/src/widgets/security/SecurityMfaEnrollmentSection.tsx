import type { FormEventHandler } from "react";

import type { MfaEnrollStartResponseDto } from "@researchlens/api-client";
import { QRCodeSVG } from "qrcode.react";

import { SecurityMfaButton } from "./SecurityMfaButton";
import { SecurityMfaField } from "./SecurityMfaField";
import { CheckCircleIcon, CopyIcon } from "./SecurityMfaIcons";

type SecurityMfaEnrollmentSectionProps = {
  copied: boolean;
  enrollment: MfaEnrollStartResponseDto;
  isWorking: boolean;
  onCopySecret: (secret: string) => Promise<void>;
  onVerificationCodeChange: (value: string) => void;
  onVerifySubmit: FormEventHandler<HTMLFormElement>;
  verificationCode: string;
};

export function SecurityMfaEnrollmentSection({
  copied,
  enrollment,
  isWorking,
  onCopySecret,
  onVerificationCodeChange,
  onVerifySubmit,
  verificationCode,
}: SecurityMfaEnrollmentSectionProps) {
  return (
    <form className="security-mfa-section" onSubmit={onVerifySubmit}>
      <div className="security-mfa-qr">
        <div className="security-mfa-qr__frame">
          <QRCodeSVG size={160} value={enrollment.otpauth_uri} />
        </div>
        <p>Scan with your authenticator app (Google Authenticator, Authy, 1Password...)</p>
      </div>

      <div className="security-mfa-detail">
        <div className="security-mfa-detail__label">Secret</div>
        <div className="security-mfa-secret">
          <code data-testid="mfa-secret">{enrollment.secret}</code>
          <button
            aria-label="Copy secret"
            className="security-mfa-copy"
            onClick={() => void onCopySecret(enrollment.secret)}
            title="Copy secret"
            type="button"
          >
            {copied ? <CheckCircleIcon className="is-success" /> : <CopyIcon />}
          </button>
        </div>
      </div>

      <div className="security-mfa-detail">
        <div className="security-mfa-detail__label">OTP URI</div>
        <p className="security-mfa-uri" title={enrollment.otpauth_uri}>
          {enrollment.otpauth_uri}
        </p>
      </div>

      <div className="security-mfa-meta">
        <div>
          <span>Issuer: </span>
          <strong>{enrollment.issuer}</strong>
        </div>
        <div>
          <span>Account: </span>
          <strong>{enrollment.account_name}</strong>
        </div>
        <div>
          <span>Period: </span>
          <strong>{enrollment.period}s</strong>
        </div>
      </div>

      <SecurityMfaField
        autoComplete="one-time-code"
        label="Verification code"
        onChange={onVerificationCodeChange}
        placeholder="123456"
        value={verificationCode}
      />

      <SecurityMfaButton fullWidth loading={isWorking} type="submit">
        {isWorking ? "Verifying..." : "Confirm and enable"}
      </SecurityMfaButton>
    </form>
  );
}
