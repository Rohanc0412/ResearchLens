import type { FormEventHandler } from "react";

import { SecurityMfaButton } from "./SecurityMfaButton";
import { SecurityMfaField } from "./SecurityMfaField";

type SecurityMfaDisableSectionProps = {
  disableCode: string;
  isWorking: boolean;
  onDisableCodeChange: (value: string) => void;
  onDisableSubmit: FormEventHandler<HTMLFormElement>;
};

export function SecurityMfaDisableSection({
  disableCode,
  isWorking,
  onDisableCodeChange,
  onDisableSubmit,
}: SecurityMfaDisableSectionProps) {
  return (
    <form className="security-mfa-section security-mfa-section--danger" onSubmit={onDisableSubmit}>
      <p className="security-mfa-copy-text">
        Enter a current TOTP code to disable multi-factor authentication.
      </p>
      <SecurityMfaField
        autoComplete="one-time-code"
        label="Current code"
        onChange={onDisableCodeChange}
        placeholder="123456"
        value={disableCode}
      />
      <SecurityMfaButton fullWidth loading={isWorking} type="submit" variant="danger">
        {isWorking ? "Disabling..." : "Disable MFA"}
      </SecurityMfaButton>
    </form>
  );
}
