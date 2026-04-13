import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";

import { LoginPage } from "./LoginPage";

const useAuthMock = vi.fn();

vi.mock("../../app/providers/AuthProvider", () => ({
  useAuth: () => useAuthMock(),
}));

vi.mock("@researchlens/api-client", () => ({
  AuthService: {
    requestPasswordResetAuthPasswordResetRequestPost: vi.fn(),
    confirmPasswordResetAuthPasswordResetConfirmPost: vi.fn(),
  },
}));

test("switches auth modes and shows matching fields", async () => {
  useAuthMock.mockReturnValue({
    status: "anonymous",
    expirationReason: null,
    login: vi.fn(),
    register: vi.fn(),
    verifyMfaChallenge: vi.fn(),
  });

  render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );

  await userEvent.setup().click(screen.getByRole("button", { name: "Register" }));
  expect(screen.getByLabelText("Username")).toBeInTheDocument();
  expect(screen.getByLabelText("Email")).toBeInTheDocument();

  await userEvent.setup().click(screen.getByRole("button", { name: "Reset confirm" }));
  expect(screen.getByLabelText("Reset token")).toBeInTheDocument();
});
