const COMMON_WEAK_PASSWORDS = new Set([
  "password",
  "password1",
  "password123",
  "password123!",
  "qwerty123",
  "letmein123",
  "admin123",
  "welcome1",
]);

export const PASSWORD_MIN_LENGTH = 8;
export const PASSWORD_MAX_LENGTH = 128;

export type PasswordRequirement = {
  id: string;
  label: string;
  message: string;
  met: boolean;
};

function normalizeIdentity(value: string | undefined) {
  return value?.trim().toLowerCase() ?? "";
}

export function getPasswordRequirements({
  password,
  username,
  email,
  includeIdentityRules,
}: {
  password: string;
  username?: string;
  email?: string;
  includeIdentityRules: boolean;
}): PasswordRequirement[] {
  const normalizedUsername = normalizeIdentity(username);
  const normalizedEmail = normalizeIdentity(email);
  const loweredPassword = password.toLowerCase();
  const requirements: PasswordRequirement[] = [
    {
      id: "length",
      label: `Use ${PASSWORD_MIN_LENGTH}-${PASSWORD_MAX_LENGTH} characters`,
      message: `Password must be ${PASSWORD_MIN_LENGTH}-${PASSWORD_MAX_LENGTH} characters.`,
      met: password.length >= PASSWORD_MIN_LENGTH && password.length <= PASSWORD_MAX_LENGTH,
    },
    {
      id: "uppercase",
      label: "Include an uppercase letter",
      message: "Password must contain at least one uppercase letter.",
      met: /[A-Z]/.test(password),
    },
    {
      id: "lowercase",
      label: "Include a lowercase letter",
      message: "Password must contain at least one lowercase letter.",
      met: /[a-z]/.test(password),
    },
    {
      id: "digit",
      label: "Include a number",
      message: "Password must contain at least one digit.",
      met: /\d/.test(password),
    },
    {
      id: "special",
      label: "Include a special character",
      message: "Password must contain at least one special character.",
      met: /[^A-Za-z0-9\s]/.test(password),
    },
    {
      id: "spaces",
      label: "Do not include spaces",
      message: "Password must not contain spaces.",
      met: !/\s/.test(password),
    },
    {
      id: "common",
      label: "Avoid common or reused passwords",
      message: "Password is too common.",
      met: !COMMON_WEAK_PASSWORDS.has(loweredPassword),
    },
  ];

  if (includeIdentityRules) {
    requirements.push(
      {
        id: "username-equals",
        label: "Must not match your username",
        message: "Password must not equal the username.",
        met: !normalizedUsername || loweredPassword !== normalizedUsername,
      },
      {
        id: "email-equals",
        label: "Must not match your email",
        message: "Password must not equal the email.",
        met: !normalizedEmail || loweredPassword !== normalizedEmail,
      },
      {
        id: "username-contains",
        label: "Must not contain your username",
        message: "Password must not contain the username.",
        met: !normalizedUsername || !loweredPassword.includes(normalizedUsername),
      },
    );
  }

  return requirements;
}

export function getFirstPasswordError(requirements: PasswordRequirement[]) {
  return requirements.find((requirement) => !requirement.met)?.message;
}
