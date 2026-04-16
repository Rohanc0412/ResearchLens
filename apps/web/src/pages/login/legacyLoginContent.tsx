import type { PropsWithChildren } from "react";

type LoginFeature = {
  icon: (props: { className?: string }) => JSX.Element;
  label: string;
};

export type LoginMode = "login" | "register" | "forgot" | "reset";

function ShieldIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 3 5 6v6c0 5 3.5 8.5 7 9 3.5-.5 7-4 7-9V6l-7-3Z" />
      <path d="m9.5 12 1.75 1.75L14.75 10" />
    </svg>
  );
}

function BrainIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" aria-hidden="true">
      <path d="M9 4a3 3 0 0 0-3 3v.5A2.5 2.5 0 0 0 4 10v1a2.5 2.5 0 0 0 2 2.45V16a3 3 0 0 0 5 2.24A3 3 0 0 0 16 16v-2.55A2.5 2.5 0 0 0 18 11v-1a2.5 2.5 0 0 0-2-2.45V7a3 3 0 0 0-5-2.24A2.98 2.98 0 0 0 9 4Z" />
      <path d="M9 10h.01M15 10h.01M10 14c.5.5 1.2.75 2 .75s1.5-.25 2-.75" />
    </svg>
  );
}

function SparklesIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" aria-hidden="true">
      <path d="m12 3 1.25 4.75L18 9l-4.75 1.25L12 15l-1.25-4.75L6 9l4.75-1.25L12 3Z" />
      <path d="m18.5 15 .6 2.4 2.4.6-2.4.6-.6 2.4-.6-2.4-2.4-.6 2.4-.6.6-2.4Z" />
      <path d="m5.5 14 .45 1.8 1.8.45-1.8.45-.45 1.8-.45-1.8-1.8-.45 1.8-.45.45-1.8Z" />
    </svg>
  );
}

function ZapIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" aria-hidden="true">
      <path d="M13 2 5 13h5l-1 9 8-11h-5l1-9Z" />
    </svg>
  );
}

const FEATURES: LoginFeature[] = [
  { icon: BrainIcon, label: "AI-powered research synthesis" },
  { icon: SparklesIcon, label: "Evidence management & tagging" },
  { icon: ZapIcon, label: "Fast, secure, team-ready" },
];

export const MODE_TITLES: Record<string, string> = {
  login: "Welcome back",
  register: "Create account",
  forgot: "Reset password",
  reset: "Set new password",
  mfa: "Verify your identity",
};

export function LegacyLoginFrame({ children }: PropsWithChildren) {
  return (
    <div className="legacy-login">
      <section className="legacy-login__brand-panel" aria-label="ResearchOps Studio overview">
        <div className="legacy-login__brand">
          <div className="legacy-login__brand-mark" aria-hidden="true">
            <ShieldIcon />
          </div>
          <span>ResearchOps Studio</span>
        </div>

        <div className="legacy-login__hero">
          <div className="legacy-login__copy">
            <h2>
              Research, organised.
              <br />
              Insights, amplified.
            </h2>
            <p>
              The AI-powered workspace for research operations teams. Run sessions, synthesise
              evidence, and surface what matters.
            </p>
          </div>

          <ul className="legacy-login__feature-list">
            {FEATURES.map(({ icon: Icon, label }) => (
              <li key={label} className="legacy-login__feature-item">
                <div className="legacy-login__feature-icon" aria-hidden="true">
                  <Icon />
                </div>
                <span>{label}</span>
              </li>
            ))}
          </ul>
        </div>

        <p className="legacy-login__copyright">
          &copy; {new Date().getFullYear()} ResearchOps Studio
        </p>
      </section>

      <main className="legacy-login__form-shell">
        <div className="legacy-login__card-wrap">{children}</div>
      </main>
    </div>
  );
}
