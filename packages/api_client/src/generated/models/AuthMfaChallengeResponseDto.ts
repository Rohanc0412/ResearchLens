/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AuthenticatedUserDto } from './AuthenticatedUserDto';
export type AuthMfaChallengeResponseDto = {
    mfa_required?: boolean;
    mfa_token: string;
    user: AuthenticatedUserDto;
};

