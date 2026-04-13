import { AuthService } from "@researchlens/api-client";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { useAuth } from "../../app/providers/AuthProvider";
import { getErrorMessage } from "../../shared/api/errors";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";
import { ErrorBanner } from "../../shared/ui/ErrorBanner";
import { Input } from "../../shared/ui/Input";
import { Page } from "../../shared/ui/Page";

export function SecurityPage() {
  const auth = useAuth();
  const [verificationCode, setVerificationCode] = useState("");
  const [disableCode, setDisableCode] = useState("");
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const status = useQuery({
    queryKey: ["auth", "mfa", "status"],
    queryFn: () => auth.authorizedRequest(() => AuthService.mfaStatusAuthMfaStatusGet()),
  });
  const enroll = useMutation({
    mutationFn: () =>
      auth.authorizedRequest(() => AuthService.startMfaEnrollmentAuthMfaEnrollStartPost()),
  });
  const verify = useMutation({
    mutationFn: (code: string) =>
      auth.authorizedRequest(() =>
        AuthService.verifyMfaEnrollmentAuthMfaEnrollVerifyPost({ code }),
      ),
    onSuccess: () => {
      void status.refetch();
      setStatusMessage("MFA enabled.");
    },
  });
  const disable = useMutation({
    mutationFn: (code: string) =>
      auth.authorizedRequest(() => AuthService.disableMfaAuthMfaDisablePost({ code })),
    onSuccess: () => {
      void status.refetch();
      setStatusMessage("MFA disabled.");
    },
  });

  return (
    <Page
      eyebrow="Security"
      title="Session hardening"
      subtitle="Manage MFA enrollment, verification state, and disable flow."
    >
      <div className="grid grid--2">
        <Card title="MFA status" meta={status.data ? JSON.stringify(status.data) : "Loading"}>
          <div className="stack">
            {statusMessage ? <Card title="Status">{statusMessage}</Card> : null}
            {status.error ? <ErrorBanner body={getErrorMessage(status.error)} /> : null}
            <div className="meta-line">
              Enabled: {status.data?.enabled ? "yes" : "no"} • Pending:{" "}
              {status.data?.pending ? "yes" : "no"}
            </div>
            <Button variant="primary" onClick={() => void enroll.mutateAsync()}>
              Start enrollment
            </Button>
            {enroll.data ? (
              <div className="stack">
                <Card title="Enrollment details">
                  <div className="meta-line">{enroll.data.otpauth_uri}</div>
                </Card>
                <Input
                  label="Verification code"
                  value={verificationCode}
                  onChange={(event) => setVerificationCode(event.target.value)}
                />
                <Button
                  variant="secondary"
                  onClick={() => void verify.mutateAsync(verificationCode)}
                >
                  Verify enrollment
                </Button>
              </div>
            ) : null}
          </div>
        </Card>

        <Card title="Disable MFA" meta="Requires a fresh TOTP code">
          <div className="stack">
            {disable.error ? <ErrorBanner body={getErrorMessage(disable.error)} /> : null}
            <Input
              label="Current code"
              value={disableCode}
              onChange={(event) => setDisableCode(event.target.value)}
            />
            <Button variant="danger" onClick={() => void disable.mutateAsync(disableCode)}>
              Disable MFA
            </Button>
          </div>
        </Card>
      </div>
    </Page>
  );
}
