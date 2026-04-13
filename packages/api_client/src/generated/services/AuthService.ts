/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AuthenticatedUserDto } from '../models/AuthenticatedUserDto';
import type { AuthMfaChallengeResponseDto } from '../models/AuthMfaChallengeResponseDto';
import type { AuthTokenResponseDto } from '../models/AuthTokenResponseDto';
import type { LoginRequestDto } from '../models/LoginRequestDto';
import type { LogoutResponseDto } from '../models/LogoutResponseDto';
import type { MfaChallengeVerifyRequestDto } from '../models/MfaChallengeVerifyRequestDto';
import type { MfaDisableRequestDto } from '../models/MfaDisableRequestDto';
import type { MfaEnabledResponseDto } from '../models/MfaEnabledResponseDto';
import type { MfaEnrollStartResponseDto } from '../models/MfaEnrollStartResponseDto';
import type { MfaEnrollVerifyRequestDto } from '../models/MfaEnrollVerifyRequestDto';
import type { MfaStatusResponseDto } from '../models/MfaStatusResponseDto';
import type { PasswordResetConfirmRequestDto } from '../models/PasswordResetConfirmRequestDto';
import type { PasswordResetConfirmResponseDto } from '../models/PasswordResetConfirmResponseDto';
import type { PasswordResetRequestDto } from '../models/PasswordResetRequestDto';
import type { PasswordResetRequestResponseDto } from '../models/PasswordResetRequestResponseDto';
import type { RegisterRequestDto } from '../models/RegisterRequestDto';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class AuthService {
    /**
     * Register
     * @param requestBody
     * @returns AuthTokenResponseDto Successful Response
     * @throws ApiError
     */
    public static registerAuthRegisterPost(
        requestBody: RegisterRequestDto,
    ): CancelablePromise<AuthTokenResponseDto> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/auth/register',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Login
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static loginAuthLoginPost(
        requestBody: LoginRequestDto,
    ): CancelablePromise<(AuthTokenResponseDto | AuthMfaChallengeResponseDto)> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/auth/login',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Refresh
     * @returns AuthTokenResponseDto Successful Response
     * @throws ApiError
     */
    public static refreshAuthRefreshPost(): CancelablePromise<AuthTokenResponseDto> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/auth/refresh',
        });
    }
    /**
     * Logout
     * @returns LogoutResponseDto Successful Response
     * @throws ApiError
     */
    public static logoutAuthLogoutPost(): CancelablePromise<LogoutResponseDto> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/auth/logout',
        });
    }
    /**
     * Me
     * @returns AuthenticatedUserDto Successful Response
     * @throws ApiError
     */
    public static meAuthMeGet(): CancelablePromise<AuthenticatedUserDto> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/auth/me',
        });
    }
    /**
     * Request Password Reset
     * @param requestBody
     * @returns PasswordResetRequestResponseDto Successful Response
     * @throws ApiError
     */
    public static requestPasswordResetAuthPasswordResetRequestPost(
        requestBody: PasswordResetRequestDto,
    ): CancelablePromise<PasswordResetRequestResponseDto> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/auth/password-reset/request',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Confirm Password Reset
     * @param requestBody
     * @returns PasswordResetConfirmResponseDto Successful Response
     * @throws ApiError
     */
    public static confirmPasswordResetAuthPasswordResetConfirmPost(
        requestBody: PasswordResetConfirmRequestDto,
    ): CancelablePromise<PasswordResetConfirmResponseDto> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/auth/password-reset/confirm',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Mfa Status
     * @returns MfaStatusResponseDto Successful Response
     * @throws ApiError
     */
    public static mfaStatusAuthMfaStatusGet(): CancelablePromise<MfaStatusResponseDto> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/auth/mfa/status',
        });
    }
    /**
     * Start Mfa Enrollment
     * @returns MfaEnrollStartResponseDto Successful Response
     * @throws ApiError
     */
    public static startMfaEnrollmentAuthMfaEnrollStartPost(): CancelablePromise<MfaEnrollStartResponseDto> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/auth/mfa/enroll/start',
        });
    }
    /**
     * Verify Mfa Enrollment
     * @param requestBody
     * @returns MfaEnabledResponseDto Successful Response
     * @throws ApiError
     */
    public static verifyMfaEnrollmentAuthMfaEnrollVerifyPost(
        requestBody: MfaEnrollVerifyRequestDto,
    ): CancelablePromise<MfaEnabledResponseDto> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/auth/mfa/enroll/verify',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Verify Mfa Challenge
     * @param requestBody
     * @returns AuthTokenResponseDto Successful Response
     * @throws ApiError
     */
    public static verifyMfaChallengeAuthMfaVerifyPost(
        requestBody: MfaChallengeVerifyRequestDto,
    ): CancelablePromise<AuthTokenResponseDto> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/auth/mfa/verify',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Disable Mfa
     * @param requestBody
     * @returns MfaEnabledResponseDto Successful Response
     * @throws ApiError
     */
    public static disableMfaAuthMfaDisablePost(
        requestBody: MfaDisableRequestDto,
    ): CancelablePromise<MfaEnabledResponseDto> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/auth/mfa/disable',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
