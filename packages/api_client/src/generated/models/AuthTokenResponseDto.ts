/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AuthenticatedUserDto } from './AuthenticatedUserDto';
export type AuthTokenResponseDto = {
    access_token: string;
    token_type?: string;
    expires_in: number;
    user: AuthenticatedUserDto;
};

