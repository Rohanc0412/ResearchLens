import {
  LegacyLoginButton,
  LegacyLoginField,
  LegacyMfaPanel,
} from "./LegacyLoginShared";

type LegacyMfaFormProps = {
  code: string;
  isSubmitting: boolean;
  userLabel: string | null;
  onCodeChange: (value: string) => void;
  onStartOver: () => void;
  onSubmit: () => void;
};

export function LegacyMfaForm({
  code,
  isSubmitting,
  userLabel,
  onCodeChange,
  onStartOver,
  onSubmit,
}: LegacyMfaFormProps) {
  return (
    <form
      className="legacy-login__stack"
      onSubmit={(event) => {
        event.preventDefault();
        void onSubmit();
      }}
    >
      <LegacyMfaPanel>
        <p>
          Enter the 6-digit code from your authenticator app
          {userLabel ? (
            <>
              {" "}
              for <span>{userLabel}</span>
            </>
          ) : null}
          .
        </p>
      </LegacyMfaPanel>

      <LegacyLoginField
        id="mfa-code"
        autoComplete="one-time-code"
        label="Verification code"
        placeholder="123456"
        value={code}
        onChange={(event) => onCodeChange(event.target.value)}
      />

      <LegacyLoginButton loading={isSubmitting} type="submit">
        {isSubmitting ? "Verifying..." : "Verify and sign in"}
      </LegacyLoginButton>
      <LegacyLoginButton onClick={onStartOver} variant="secondary">
        Use a different account
      </LegacyLoginButton>
    </form>
  );
}
