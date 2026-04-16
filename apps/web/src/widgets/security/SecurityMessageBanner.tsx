import { CheckCircleIcon } from "./SecurityMfaIcons";

type SecurityMessageBannerProps = {
  message: string;
  variant: "error" | "success";
};

export function SecurityMessageBanner({
  message,
  variant,
}: SecurityMessageBannerProps) {
  return (
    <section
      className={`security-mfa-banner security-mfa-banner--${variant}`}
      role={variant === "error" ? "alert" : "status"}
    >
      {variant === "success" ? <CheckCircleIcon /> : null}
      <div className="security-mfa-banner__copy">
        {variant === "error" ? <p className="security-mfa-banner__title">Security error</p> : null}
        <p>{message}</p>
      </div>
    </section>
  );
}
