/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ConversationListResponse } from '../models/ConversationListResponse';
import type { ConversationResponse } from '../models/ConversationResponse';
import type { CreateConversationRequest } from '../models/CreateConversationRequest';
import type { UpdateConversationRequest } from '../models/UpdateConversationRequest';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class ConversationsService {
    /**
     * Create Conversation
     * @param projectId
     * @param requestBody
     * @returns ConversationResponse Successful Response
     * @throws ApiError
     */
    public static createConversationProjectsProjectIdConversationsPost(
        projectId: string,
        requestBody: CreateConversationRequest,
    ): CancelablePromise<ConversationResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/projects/{project_id}/conversations',
            path: {
                'project_id': projectId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Conversations
     * @param projectId
     * @param cursor
     * @param limit
     * @returns ConversationListResponse Successful Response
     * @throws ApiError
     */
    public static listConversationsProjectsProjectIdConversationsGet(
        projectId: string,
        cursor?: (string | null),
        limit: number = 20,
    ): CancelablePromise<ConversationListResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/projects/{project_id}/conversations',
            path: {
                'project_id': projectId,
            },
            query: {
                'cursor': cursor,
                'limit': limit,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Conversation
     * @param conversationId
     * @returns ConversationResponse Successful Response
     * @throws ApiError
     */
    public static getConversationConversationsConversationIdGet(
        conversationId: string,
    ): CancelablePromise<ConversationResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/conversations/{conversation_id}',
            path: {
                'conversation_id': conversationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update Conversation
     * @param conversationId
     * @param requestBody
     * @returns ConversationResponse Successful Response
     * @throws ApiError
     */
    public static updateConversationConversationsConversationIdPatch(
        conversationId: string,
        requestBody: UpdateConversationRequest,
    ): CancelablePromise<ConversationResponse> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/conversations/{conversation_id}',
            path: {
                'conversation_id': conversationId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete Conversation
     * @param conversationId
     * @returns void
     * @throws ApiError
     */
    public static deleteConversationConversationsConversationIdDelete(
        conversationId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/conversations/{conversation_id}',
            path: {
                'conversation_id': conversationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
