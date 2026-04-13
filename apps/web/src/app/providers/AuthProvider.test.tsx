import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import { AuthProvider, useAuth } from "./AuthProvider";

const mocks = vi.hoisted(() => ({
  refresh: vi.fn(),
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
  verifyMfa: vi.fn(),
  ApiError: class MockApiError extends Error {
    status: number;

    constructor(status: number) {
      super(`status ${status}`);
      this.status = status;
    }
  },
}));

vi.mock("@researchlens/api-client", () => ({
  AuthService: {
    refreshAuthRefreshPost: mocks.refresh,
    loginAuthLoginPost: mocks.login,
    registerAuthRegisterPost: mocks.register,
    logoutAuthLogoutPost: mocks.logout,
    verifyMfaChallengeAuthMfaVerifyPost: mocks.verifyMfa,
  },
  ApiError: mocks.ApiError,
  OpenAPI: {},
}));

function Probe() {
  const auth = useAuth();

  return (
    <div>
      <div data-testid="status">{auth.status}</div>
      <div data-testid="user">{auth.user?.username ?? "none"}</div>
      <button
        type="button"
        onClick={() =>
          void auth
            .authorizedRequest(async () => "ok")
            .then((value) => {
              document.body.dataset.result = value;
            })
        }
      >
        call
      </button>
    </div>
  );
}

describe("AuthProvider", () => {
  beforeEach(() => {
    mocks.refresh.mockReset();
    mocks.login.mockReset();
    mocks.register.mockReset();
    mocks.logout.mockReset();
    mocks.verifyMfa.mockReset();
    delete document.body.dataset.result;
  });

  test("restores the session from refresh on bootstrap", async () => {
    mocks.refresh.mockResolvedValue({
      access_token: "token-1",
      expires_in: 900,
      token_type: "bearer",
      user: {
        user_id: "user-1",
        username: "casey",
        email: "casey@example.com",
        tenant_id: "tenant-1",
        roles: ["user"],
      },
    });

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );

    await waitFor(() => expect(screen.getByTestId("status")).toHaveTextContent("authenticated"));
    expect(screen.getByTestId("user")).toHaveTextContent("casey");
  });

  test("retries an authorized request after a 401 refresh", async () => {
    mocks.refresh
      .mockResolvedValueOnce({
        access_token: "boot-token",
        expires_in: 900,
        token_type: "bearer",
        user: {
          user_id: "user-1",
          username: "casey",
          email: "casey@example.com",
          tenant_id: "tenant-1",
          roles: ["user"],
        },
      })
      .mockResolvedValueOnce({
        access_token: "refreshed-token",
        expires_in: 900,
        token_type: "bearer",
        user: {
          user_id: "user-1",
          username: "casey",
          email: "casey@example.com",
          tenant_id: "tenant-1",
          roles: ["user"],
        },
      });

    let attempts = 0;

    function RetryProbe() {
      const auth = useAuth();
      return (
        <button
          type="button"
          onClick={() =>
            void auth
                  .authorizedRequest(async () => {
                attempts += 1;
                if (attempts === 1) {
                  throw new mocks.ApiError(401);
                }
                document.body.dataset.result = "retried";
                return "retried";
              })
          }
        >
          retry
        </button>
      );
    }

    render(
      <AuthProvider>
        <RetryProbe />
      </AuthProvider>,
    );

    await waitFor(() => expect(mocks.refresh).toHaveBeenCalledTimes(1));
    await userEvent.setup().click(screen.getByRole("button", { name: "retry" }));
    await waitFor(() => expect(document.body.dataset.result).toBe("retried"));
    expect(mocks.refresh).toHaveBeenCalledTimes(2);
  });
});
