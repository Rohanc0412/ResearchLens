import { AuthService, type MfaEnrollStartResponseDto } from "@researchlens/api-client";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useRef, useState, type FormEvent } from "react";

import { useAuth } from "../../app/providers/AuthProvider";
import { getErrorMessage } from "../../shared/api/errors";

const START_ERROR = "Unable to start MFA enrollment.";
const VERIFY_ERROR = "Verification failed.";
const DISABLE_ERROR = "Disable failed.";
const COPY_ERROR = "Unable to copy the MFA secret.";

function getVerificationError(error: unknown) {
  const raw = getErrorMessage(error, VERIFY_ERROR);
  return raw.includes("401")
    ? "Invalid verification code. Please check your authenticator app and try again."
    : raw;
}

function getDisableError(error: unknown) {
  const raw = getErrorMessage(error, DISABLE_ERROR);
  return raw.includes("422") || raw.includes("401")
    ? "Invalid TOTP code. Please check your authenticator app and try again."
    : raw;
}

export function useSecurityMfa() {
  const auth = useAuth();
  const copyResetRef = useRef<number | null>(null);
  const [enrollment, setEnrollment] = useState<MfaEnrollStartResponseDto | null>(null);
  const [verificationCode, setVerificationCode] = useState("");
  const [disableCode, setDisableCode] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isWorking, setIsWorking] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(
    () => () => {
      if (copyResetRef.current !== null) {
        window.clearTimeout(copyResetRef.current);
      }
    },
    [],
  );

  const statusQuery = useQuery({
    queryKey: ["auth", "mfa", "status"],
    queryFn: () => auth.authorizedRequest(() => AuthService.mfaStatusAuthMfaStatusGet()),
  });

  const enabled = statusQuery.data?.enabled ?? false;
  const pending = statusQuery.data?.pending ?? false;

  function clearFeedback() {
    setErrorMessage(null);
    setSuccessMessage(null);
  }

  async function handleStart() {
    clearFeedback();
    setIsWorking(true);
    try {
      const data = await auth.authorizedRequest(() =>
        AuthService.startMfaEnrollmentAuthMfaEnrollStartPost(),
      );
      setEnrollment(data);
      setSuccessMessage("Scan the secret in your authenticator app and enter the code below.");
    } catch (error) {
      setErrorMessage(getErrorMessage(error, START_ERROR));
    } finally {
      setIsWorking(false);
    }
  }

  async function handleVerify(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    clearFeedback();
    setIsWorking(true);
    try {
      await auth.authorizedRequest(() =>
        AuthService.verifyMfaEnrollmentAuthMfaEnrollVerifyPost({ code: verificationCode }),
      );
      setVerificationCode("");
      setEnrollment(null);
      await statusQuery.refetch();
      setSuccessMessage("MFA is enabled.");
    } catch (error) {
      setVerificationCode("");
      setErrorMessage(getVerificationError(error));
    } finally {
      setIsWorking(false);
    }
  }

  async function handleDisable(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    clearFeedback();
    if (!disableCode.trim()) {
      setErrorMessage("Please enter your current TOTP code before disabling MFA.");
      return;
    }

    setIsWorking(true);
    try {
      await auth.authorizedRequest(() =>
        AuthService.disableMfaAuthMfaDisablePost({ code: disableCode }),
      );
      setDisableCode("");
      await statusQuery.refetch();
      setSuccessMessage("MFA is disabled.");
    } catch (error) {
      setErrorMessage(getDisableError(error));
    } finally {
      setIsWorking(false);
    }
  }

  async function handleCopySecret(secret: string) {
    try {
      await navigator.clipboard.writeText(secret);
      setCopied(true);
      if (copyResetRef.current !== null) {
        window.clearTimeout(copyResetRef.current);
      }
      copyResetRef.current = window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setErrorMessage(COPY_ERROR);
    }
  }

  return {
    copied,
    disableCode,
    enabled,
    enrollment,
    errorMessage,
    handleCopySecret,
    handleDisable,
    handleStart,
    handleVerify,
    isWorking,
    pending,
    setDisableCode,
    setVerificationCode,
    statusLoading: statusQuery.isLoading,
    successMessage,
    verificationCode,
  };
}
