import {
  AuthService,
  type AuthMfaChallengeResponseDto,
  type AuthTokenResponseDto,
  type AuthenticatedUserDto,
  ApiError,
} from "@researchlens/api-client";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type PropsWithChildren,
} from "react";

import { configureApiClient } from "../../shared/api/client";

type SessionStatus = "bootstrapping" | "anonymous" | "authenticated" | "mfa_challenge";

type LoginPayload = {
  identifier: string;
  password: string;
};

type RegisterPayload = {
  username: string;
  email: string;
  password: string;
};

type PendingMfaChallenge = AuthMfaChallengeResponseDto & {
  identifier: string;
};

type AuthContextValue = {
  status: SessionStatus;
  user: AuthenticatedUserDto | null;
  accessToken: string | null;
  challenge: PendingMfaChallenge | null;
  expirationReason: "expired" | "logout" | null;
  login: (payload: LoginPayload) => Promise<"authenticated" | "mfa_required">;
  register: (payload: RegisterPayload) => Promise<void>;
  verifyMfaChallenge: (code: string) => Promise<void>;
  restoreSession: () => Promise<string | null>;
  authorizedRequest: <T>(request: () => Promise<T>, skipRefresh?: boolean) => Promise<T>;
  logout: () => Promise<void>;
  clearExpirationReason: () => void;
  completeSession: (response: AuthTokenResponseDto) => void;
  clearSession: (reason?: "expired" | "logout") => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

function isUnauthorized(error: unknown) {
  return error instanceof ApiError && error.status === 401;
}

function isMfaChallengeResponse(
  response: AuthMfaChallengeResponseDto | AuthTokenResponseDto,
): response is AuthMfaChallengeResponseDto {
  return "mfa_required" in response;
}

export function AuthProvider({ children }: PropsWithChildren) {
  const accessTokenRef = useRef<string | null>(null);
  const refreshPromiseRef = useRef<Promise<AuthTokenResponseDto> | null>(null);
  const [status, setStatus] = useState<SessionStatus>("bootstrapping");
  const [user, setUser] = useState<AuthenticatedUserDto | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [challenge, setChallenge] = useState<PendingMfaChallenge | null>(null);
  const [expirationReason, setExpirationReason] = useState<"expired" | "logout" | null>(
    null,
  );

  useEffect(() => {
    accessTokenRef.current = accessToken;
  }, [accessToken]);

  useEffect(() => {
    configureApiClient(() => accessTokenRef.current);
  }, []);

  const clearSession = useCallback((reason?: "expired" | "logout") => {
    accessTokenRef.current = null;
    setAccessToken(null);
    setUser(null);
    setChallenge(null);
    setStatus("anonymous");
    setExpirationReason(reason ?? null);
  }, []);

  const completeSession = useCallback((response: AuthTokenResponseDto) => {
    accessTokenRef.current = response.access_token;
    setAccessToken(response.access_token);
    setUser(response.user);
    setChallenge(null);
    setStatus("authenticated");
    setExpirationReason(null);
  }, []);

  const refreshSession = useCallback(async () => {
    if (refreshPromiseRef.current) {
      return refreshPromiseRef.current;
    }

    const promise = AuthService.refreshAuthRefreshPost()
      .then((response) => {
        completeSession(response);
        return response;
      })
      .finally(() => {
        refreshPromiseRef.current = null;
      });

    refreshPromiseRef.current = promise;
    return promise;
  }, [completeSession]);

  const restoreSession = useCallback(async () => {
    try {
      const response = await refreshSession();
      return response.access_token;
    } catch {
      clearSession();
      return null;
    }
  }, [clearSession, refreshSession]);

  useEffect(() => {
    void restoreSession();
  }, [restoreSession]);

  const authorizedRequest = useCallback(
    async <T,>(request: () => Promise<T>, skipRefresh = false) => {
      try {
        return await request();
      } catch (error) {
        if (skipRefresh || !isUnauthorized(error)) {
          throw error;
        }

        try {
          await refreshSession();
        } catch {
          clearSession("expired");
          throw error;
        }

        return request();
      }
    },
    [clearSession, refreshSession],
  );

  const login = useCallback(async (payload: LoginPayload) => {
    const response = await AuthService.loginAuthLoginPost(payload);
    if (isMfaChallengeResponse(response) && response.mfa_required) {
      setChallenge({ ...response, identifier: payload.identifier });
      setUser(response.user);
      setStatus("mfa_challenge");
      return "mfa_required" as const;
    }
    completeSession(response as AuthTokenResponseDto);
    return "authenticated" as const;
  }, [completeSession]);

  const register = useCallback(async (payload: RegisterPayload) => {
    const response = await AuthService.registerAuthRegisterPost(payload);
    completeSession(response);
  }, [completeSession]);

  const verifyMfaChallenge = useCallback(async (code: string) => {
    if (!challenge) {
      throw new Error("No MFA challenge is currently active.");
    }
    const response = await AuthService.verifyMfaChallengeAuthMfaVerifyPost({
      code,
      mfa_token: challenge.mfa_token,
    });
    completeSession(response);
  }, [challenge, completeSession]);

  const logout = useCallback(async () => {
    try {
      await AuthService.logoutAuthLogoutPost();
    } finally {
      clearSession("logout");
    }
  }, [clearSession]);

  const value = useMemo<AuthContextValue>(
    () => ({
      status,
      user,
      accessToken,
      challenge,
      expirationReason,
      login,
      register,
      verifyMfaChallenge,
      restoreSession,
      authorizedRequest,
      logout,
      clearExpirationReason: () => setExpirationReason(null),
      completeSession,
      clearSession,
    }),
    [
      accessToken,
      authorizedRequest,
      challenge,
      clearSession,
      completeSession,
      expirationReason,
      login,
      logout,
      register,
      restoreSession,
      status,
      user,
      verifyMfaChallenge,
    ],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) {
    throw new Error("useAuth must be used within AuthProvider.");
  }
  return value;
}
