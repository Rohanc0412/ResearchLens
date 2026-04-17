import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";

import { LoginPage } from "./LoginPage";

const useAuthMock = vi.fn();
const {
  confirmPasswordResetMock,
  logoutMock,
  registerMock,
  requestPasswordResetMock,
} = vi.hoisted(() => ({
  confirmPasswordResetMock: vi.fn(),
  logoutMock: vi.fn(),
  registerMock: vi.fn(),
  requestPasswordResetMock: vi.fn(),
}));

vi.mock("../../app/providers/AuthProvider", () => ({
  useAuth: () => useAuthMock(),
}));

vi.mock("@researchlens/api-client", () => ({
  AuthService: {
    confirmPasswordResetAuthPasswordResetConfirmPost: confirmPasswordResetMock,
    logoutAuthLogoutPost: logoutMock,
    registerAuthRegisterPost: registerMock,
    requestPasswordResetAuthPasswordResetRequestPost: requestPasswordResetMock,
  },
}));

function renderLoginPage() {
  return render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  confirmPasswordResetMock.mockReset();
  logoutMock.mockReset();
  registerMock.mockReset();
  requestPasswordResetMock.mockReset();
  window.sessionStorage.clear();
});

test("renders the restored legacy login shell", () => {
  useAuthMock.mockReturnValue({
    challenge: null,
    clearExpirationReason: vi.fn(),
    clearSession: vi.fn(),
    expirationReason: null,
    login: vi.fn(),
    status: "bootstrapping",
    user: null,
    verifyMfaChallenge: vi.fn(),
  });

  renderLoginPage();

  expect(screen.getByRole("heading", { name: "Welcome back" })).toBeInTheDocument();
  expect(screen.getByText("ResearchOps Studio")).toBeInTheDocument();
  expect(screen.getByText("AI-powered research synthesis")).toBeInTheDocument();
});

test("switches into register and reset flows", async () => {
  requestPasswordResetMock.mockResolvedValue({});
  useAuthMock.mockReturnValue({
    challenge: null,
    clearExpirationReason: vi.fn(),
    clearSession: vi.fn(),
    expirationReason: null,
    login: vi.fn(),
    status: "anonymous",
    user: null,
    verifyMfaChallenge: vi.fn(),
  });

  renderLoginPage();
  const user = userEvent.setup();

  await user.click(screen.getByRole("button", { name: "Create one" }));
  expect(await screen.findByLabelText("Email")).toBeInTheDocument();
  expect(await screen.findByLabelText("Confirm password")).toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "Sign in" }));
  await user.click(screen.getByRole("button", { name: "Forgot password?" }));
  await user.type(screen.getByLabelText("Email"), "owner@company.com");
  await user.click(screen.getByRole("button", { name: "Email reset code" }));

  await waitFor(() =>
    expect(requestPasswordResetMock).toHaveBeenCalledWith({ email: "owner@company.com" }),
  );
  expect(await screen.findByLabelText("Reset code")).toBeInTheDocument();
  expect(
    screen.getByText("If the account exists, a reset code was sent to your email. Enter it below to reset your password."),
  ).toBeInTheDocument();
});

test("registers and returns to sign in with the legacy success banner", async () => {
  registerMock.mockResolvedValue({});
  logoutMock.mockResolvedValue({ status: "ok" });
  useAuthMock.mockReturnValue({
    challenge: null,
    clearExpirationReason: vi.fn(),
    clearSession: vi.fn(),
    expirationReason: null,
    login: vi.fn(),
    status: "anonymous",
    user: null,
    verifyMfaChallenge: vi.fn(),
  });

  renderLoginPage();
  const user = userEvent.setup();

  await user.click(screen.getByRole("button", { name: "Create one" }));
  await user.type(screen.getByLabelText("Username or email"), "alice");
  await user.type(screen.getByLabelText("Email"), "alice@example.com");
  await user.type(screen.getByLabelText("Password"), "password123");
  await user.type(screen.getByLabelText("Confirm password"), "password123");
  await user.click(screen.getByRole("button", { name: "Create account" }));

  await waitFor(() =>
    expect(registerMock).toHaveBeenCalledWith({
      email: "alice@example.com",
      password: "password123",
      username: "alice",
    }),
  );
  await waitFor(() => expect(logoutMock).toHaveBeenCalled());
  expect(
    await screen.findByText("Account created successfully! You can now sign in."),
  ).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Sign in" })).toBeInTheDocument();
});

test("lets the user cancel an MFA challenge and use a different account", async () => {
  const clearSession = vi.fn();
  useAuthMock.mockReturnValue({
    challenge: { identifier: "owner@company.com" },
    clearExpirationReason: vi.fn(),
    clearSession,
    expirationReason: null,
    login: vi.fn(),
    status: "mfa_challenge",
    user: null,
    verifyMfaChallenge: vi.fn(),
  });

  renderLoginPage();
  const user = userEvent.setup();

  expect(await screen.findByLabelText("Verification code")).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "Use a different account" }));
  expect(clearSession).toHaveBeenCalled();
});
