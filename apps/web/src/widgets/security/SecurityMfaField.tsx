type SecurityMfaFieldProps = {
  autoComplete?: string;
  label: string;
  onChange: (value: string) => void;
  placeholder?: string;
  value: string;
};

export function SecurityMfaField({
  autoComplete,
  label,
  onChange,
  placeholder,
  value,
}: SecurityMfaFieldProps) {
  return (
    <label className="security-mfa-field">
      <span>{label}</span>
      <input
        autoComplete={autoComplete}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        value={value}
      />
    </label>
  );
}
