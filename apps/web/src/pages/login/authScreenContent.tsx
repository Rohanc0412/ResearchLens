export type LoginMode = "login" | "register" | "request_reset" | "confirm_reset";
export type AuthStepId = "access" | "recovery" | "verification";

export type AuthViewCopy = {
  eyebrow: string;
  title: string;
  body: string;
  primaryLabel: string;
  badges: string[];
  supportTitle: string;
  supportBody: string;
  footer: string;
};

const AUTH_STEPS: { id: AuthStepId; label: string; detail: string }[] = [
  {
    id: "access",
    label: "Access",
    detail: "Use workspace credentials and restore active sessions safely.",
  },
  {
    id: "recovery",
    label: "Recover",
    detail: "Reset credentials with explicit recovery tokens and password policy checks.",
  },
  {
    id: "verification",
    label: "Verify",
    detail: "Finish elevated sign-in with a second factor before a session is issued.",
  },
];

const TRUST_HIGHLIGHTS = [
  {
    title: "Evidence-linked outputs",
    description:
      "Projects, conversations, and export artifacts stay anchored to sources and review history.",
    icon: AuthSourceIcon,
  },
  {
    title: "Hardened session model",
    description:
      "Short-lived access tokens, refresh rotation, and MFA support keep workspace access explicit.",
    icon: AuthShieldIcon,
  },
  {
    title: "Recovery without ambiguity",
    description:
      "Password reset and MFA verification are staged flows with visible feedback at each step.",
    icon: AuthRecoveryIcon,
  },
];

export const AUTH_COPY: Record<LoginMode | "mfa", AuthViewCopy> = {
  login: {
    eyebrow: "Workspace access",
    title: "Sign in to continue your research run.",
    body:
      "Use your ResearchLens workspace credentials to reopen projects, conversations, and evidence reviews without losing the original destination.",
    primaryLabel: "Sign in",
    badges: ["Session restore", "MFA ready", "Tenant scoped"],
    supportTitle: "What happens after sign-in",
    supportBody:
      "You return to the protected route that triggered authentication, with refresh-cookie session recovery available on the next visit.",
    footer:
      "Access is tenant-scoped and managed through explicit token rotation rules.",
  },
  register: {
    eyebrow: "Workspace setup",
    title: "Create a secure ResearchLens workspace account.",
    body:
      "Register with a username, work email, and policy-compliant password. The session is established immediately after successful account creation.",
    primaryLabel: "Create workspace",
    badges: ["Password policy", "Immediate session", "MFA available"],
    supportTitle: "Industry-standard onboarding",
    supportBody:
      "Account creation stays minimal: identity, work email, strong password, then continue directly into the product.",
    footer:
      "Password guidance is enforced inline so weak credentials never advance.",
  },
  request_reset: {
    eyebrow: "Account recovery",
    title: "Request a password reset token.",
    body:
      "Enter the email connected to your workspace. ResearchLens issues a reset token through the configured delivery channel and keeps the recovery step explicit.",
    primaryLabel: "Send reset token",
    badges: ["Recovery token", "Clear status", "No silent fallback"],
    supportTitle: "Recovery flow design",
    supportBody:
      "The reset request is separate from password entry so users always know whether they are requesting access or setting a new credential.",
    footer:
      "Password reset requests return a visible status message instead of redirecting silently.",
  },
  confirm_reset: {
    eyebrow: "Credential reset",
    title: "Set a new password with your reset token.",
    body:
      "Paste the issued recovery token, choose a compliant password, and return to the sign-in flow with the updated credential.",
    primaryLabel: "Update password",
    badges: ["Token required", "Policy checked", "Explicit completion"],
    supportTitle: "Recovery safeguards",
    supportBody:
      "Recovery confirmation keeps the token and password in one focused step, with no ambiguous multi-form state changes.",
    footer:
      "The updated password must still satisfy identity-aware password rules.",
  },
  mfa: {
    eyebrow: "Multi-factor verification",
    title: "Verify the sign-in request.",
    body:
      "The account password was accepted. Enter the current six-digit authenticator code to finish issuing the session for this login attempt.",
    primaryLabel: "Verify challenge",
    badges: ["Challenge bound", "6-digit code", "Session not issued yet"],
    supportTitle: "Second-factor checkpoint",
    supportBody:
      "The MFA challenge remains tied to the pending sign-in attempt. Starting over clears the unfinished challenge before any access token is granted.",
    footer:
      "Verification finishes the existing sign-in attempt rather than creating a separate session.",
  },
};

export function AuthStepRail({ activeStep }: { activeStep: AuthStepId }) {
  return (
    <ol className="auth-step-rail" aria-label="Authentication stages">
      {AUTH_STEPS.map((step, index) => {
        const isActive = step.id === activeStep;
        const isCompleted = AUTH_STEPS.findIndex((entry) => entry.id === activeStep) > index;
        return (
          <li
            key={step.id}
            className="auth-step-rail__item"
            data-active={isActive}
            data-complete={isCompleted}
          >
            <span className="auth-step-rail__count" aria-hidden="true">
              {index + 1}
            </span>
            <div>
              <strong>{step.label}</strong>
              <p>{step.detail}</p>
            </div>
          </li>
        );
      })}
    </ol>
  );
}

export function AuthOverviewPanel() {
  return (
    <aside className="auth-panel" aria-label="ResearchLens overview">
      <div className="auth-brand">
        <span className="auth-brand__mark" aria-hidden="true">
          <AuthBrandIcon />
        </span>
        <div className="auth-brand__meta">
          <span className="auth-brand__eyebrow">Secure Research Workspace</span>
          <span>ResearchLens</span>
        </div>
      </div>
      <div className="auth-copy">
        <span className="auth-copy__eyebrow">Trust-first authentication</span>
        <h1>Defensible research work starts with a clear access flow.</h1>
        <p>
          ResearchLens is built for teams that need secure project access, visible evidence
          lineage, and explicit control over session recovery.
        </p>
      </div>
      <div className="auth-overview-grid" aria-label="ResearchLens trust highlights">
        {TRUST_HIGHLIGHTS.map((highlight) => {
          const Icon = highlight.icon;
          return (
            <article key={highlight.title} className="auth-overview-card">
              <span className="auth-overview-card__icon" aria-hidden="true">
                <Icon />
              </span>
              <div className="auth-overview-card__body">
                <strong>{highlight.title}</strong>
                <p>{highlight.description}</p>
              </div>
            </article>
          );
        })}
      </div>
      <div className="auth-proof-grid" aria-label="Workspace operating model">
        <article className="auth-proof-card">
          <span className="auth-proof-card__label">Session security</span>
          <strong>Refresh restore, token rotation, and explicit MFA checkpoints</strong>
          <p>Login, recovery, and verification are separate states with visible completion.</p>
        </article>
        <article className="auth-proof-card">
          <span className="auth-proof-card__label">Research integrity</span>
          <strong>Projects and artifacts remain linked to evidence and review trails</strong>
          <p>Access control protects the same audit-friendly workspace used for final outputs.</p>
        </article>
      </div>
      <p className="auth-copyright">&copy; 2026 ResearchLens</p>
    </aside>
  );
}

function AuthBrandIcon() {
  return (
    <svg viewBox="0 0 24 24" role="img">
      <path d="M12 3.25 5.75 5.6v4.95c0 4.05 2.55 7.75 6.25 9.15 3.7-1.4 6.25-5.1 6.25-9.15V5.6L12 3.25Z" />
      <path d="M9.25 11.75 11.2 13.7l3.55-3.9" />
    </svg>
  );
}

function AuthShieldIcon() {
  return (
    <svg viewBox="0 0 24 24" role="img">
      <path d="M12 3.5 6.5 5.6v5.55c0 3.6 2.15 6.85 5.5 8.35 3.35-1.5 5.5-4.75 5.5-8.35V5.6L12 3.5Z" />
      <path d="M9.5 12.25 11.1 13.85l3.4-3.7" />
    </svg>
  );
}

function AuthSourceIcon() {
  return (
    <svg viewBox="0 0 24 24" role="img">
      <path d="M6.25 6.75h11.5" />
      <path d="M6.25 11.75h11.5" />
      <path d="M6.25 16.75h7.25" />
      <path d="M4.75 4.5h14.5a1.25 1.25 0 0 1 1.25 1.25v12.5a1.25 1.25 0 0 1-1.25 1.25H4.75A1.25 1.25 0 0 1 3.5 18.25V5.75A1.25 1.25 0 0 1 4.75 4.5Z" />
    </svg>
  );
}

function AuthRecoveryIcon() {
  return (
    <svg viewBox="0 0 24 24" role="img">
      <path d="M7.25 8.75A5.25 5.25 0 0 1 12 6a5.25 5.25 0 0 1 4.75 2.75" />
      <path d="M7.25 8.75V5.5" />
      <path d="M7.25 8.75h3.1" />
      <path d="M16.75 15.25A5.25 5.25 0 0 1 12 18a5.25 5.25 0 0 1-4.75-2.75" />
      <path d="M16.75 15.25v3.25" />
      <path d="M13.65 15.25h3.1" />
      <path d="M12 9.75v2.75l1.9 1.25" />
    </svg>
  );
}
