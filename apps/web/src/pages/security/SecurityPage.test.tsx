import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import { SecurityPage } from "./SecurityPage";

const useAuthMock = vi.fn();
const {
  disableMfaMock,
  mfaStatusMock,
  startMfaEnrollmentMock,
  verifyMfaEnrollmentMock,
} = vi.hoisted(() => ({
  disableMfaMock: vi.fn(),
  mfaStatusMock: vi.fn(),
  startMfaEnrollmentMock: vi.fn(),
  verifyMfaEnrollmentMock: vi.fn(),
}));

vi.mock("../../app/providers/AuthProvider", () => ({
  useAuth: () => useAuthMock(),
}));

vi.mock("@researchlens/api-client", () => ({
  AuthService: {
    disableMfaAuthMfaDisablePost: disableMfaMock,
    mfaStatusAuthMfaStatusGet: mfaStatusMock,
    startMfaEnrollmentAuthMfaEnrollStartPost: startMfaEnrollmentMock,
    verifyMfaEnrollmentAuthMfaEnrollVerifyPost: verifyMfaEnrollmentMock,
  },
}));

function renderSecurityPage() {
  return render(
    <QueryClientProvider client={new QueryClient()}>
      <SecurityPage />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  disableMfaMock.mockReset();
  mfaStatusMock.mockReset();
  startMfaEnrollmentMock.mockReset();
  verifyMfaEnrollmentMock.mockReset();
  useAuthMock.mockReturnValue({
    authorizedRequest: (request: () => Promise<unknown>) => request(),
  });
});

test("renders the old MFA enrollment experience with QR setup details", async () => {
  mfaStatusMock.mockResolvedValue({ enabled: false, pending: false });
  startMfaEnrollmentMock.mockResolvedValue({
    account_name: "owner@example.com",
    digits: 6,
    issuer: "ResearchLens",
    otpauth_uri: "otpauth://totp/ResearchLens:owner@example.com?secret=ABC123",
    period: 30,
    secret: "ABC123",
  });

  renderSecurityPage();
  const user = userEvent.setup();

  expect(await screen.findByRole("heading", { name: "Security" })).toBeInTheDocument();
  expect(screen.getByText("Manage multi-factor authentication for your account.")).toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "Enable MFA" }));

  await waitFor(() => expect(startMfaEnrollmentMock).toHaveBeenCalled());
  expect(await screen.findByText(/Scan with your authenticator app/)).toBeInTheDocument();
  expect(screen.getByTestId("mfa-secret")).toHaveTextContent("ABC123");
  expect(screen.getByRole("button", { name: "Confirm and enable" })).toBeInTheDocument();
});

test("shows the disable form when MFA is already enabled", async () => {
  mfaStatusMock.mockResolvedValue({ enabled: true, pending: false });

  renderSecurityPage();

  expect(await screen.findByText("Authenticator app (TOTP)")).toBeInTheDocument();
  expect(
    await screen.findByText("Enter a current TOTP code to disable multi-factor authentication."),
  ).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Disable MFA" })).toBeInTheDocument();
});
