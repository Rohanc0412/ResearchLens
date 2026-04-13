/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { MessageResponse } from '../models/MessageResponse';
import type { MessageWriteResponse } from '../models/MessageWriteResponse';
import type { PostMessageRequest } from '../models/PostMessageRequest';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class MessagesService {
    /**
     * Post Message
     * @param conversationId
     * @param requestBody
     * @returns MessageWriteResponse Successful Response
     * @throws ApiError
     */
    public static postMessageConversationsConversationIdMessagesPost(
        conversationId: string,
        requestBody: PostMessageRequest,
    ): CancelablePromise<MessageWriteResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/conversations/{conversation_id}/messages',
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
     * List Messages
     * @param conversationId
     * @returns MessageResponse Successful Response
     * @throws ApiError
     */
    public static listMessagesConversationsConversationIdMessagesGet(
        conversationId: string,
    ): CancelablePromise<Array<MessageResponse>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/conversations/{conversation_id}/messages',
            path: {
                'conversation_id': conversationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Message
     * @param conversationId
     * @param messageId
     * @returns MessageResponse Successful Response
     * @throws ApiError
     */
    public static getMessageConversationsConversationIdMessagesMessageIdGet(
        conversationId: string,
        messageId: string,
    ): CancelablePromise<MessageResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/conversations/{conversation_id}/messages/{message_id}',
            path: {
                'conversation_id': conversationId,
                'message_id': messageId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
