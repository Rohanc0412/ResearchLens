function CheckCircleIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20Z" />
      <path d="m8 12 2.5 2.5L16 9" />
    </svg>
  );
}

export function LegacyLoginErrorBanner({ message }: { message: string }) {
  return (
    <section className="legacy-login__error-banner" role="alert">
      <div className="legacy-login__error-copy">
        <p className="legacy-login__error-title">Something went wrong</p>
        <p>{message}</p>
      </div>
    </section>
  );
}

export function LegacyLoginSuccessBanner({ message }: { message: string }) {
  return (
    <section className="legacy-login__success-banner" role="status" aria-live="polite">
      <CheckCircleIcon />
      <p>{message}</p>
    </section>
  );
}
