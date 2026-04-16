import type { PasswordRequirement } from "./passwordPolicy";

export function PasswordChecklist({
  requirements,
  identityReminder,
  className,
}: {
  requirements: PasswordRequirement[];
  identityReminder?: string;
  className?: string;
}) {
  return (
    <div className={["password-checklist", className].filter(Boolean).join(" ")} aria-live="polite">
      <p className="password-checklist__title">Password requirements</p>
      <ul className="password-checklist__list">
        {requirements.map((requirement) => (
          <li
            key={requirement.id}
            className="password-checklist__item"
            data-met={requirement.met}
          >
            <span className="password-checklist__icon" aria-hidden="true">
              {requirement.met ? "✓" : "·"}
            </span>
            <span>{requirement.label}</span>
          </li>
        ))}
      </ul>
      {identityReminder ? (
        <p className="password-checklist__note">{identityReminder}</p>
      ) : null}
    </div>
  );
}
