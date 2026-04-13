/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CreateRunRequest } from '../models/CreateRunRequest';
import type { CreateRunResponse } from '../models/CreateRunResponse';
import type { RunEventResponse } from '../models/RunEventResponse';
import type { RunSummaryResponse } from '../models/RunSummaryResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class RunsService {
    /**
     * Create Run
     * @param conversationId
     * @param requestBody
     * @returns CreateRunResponse Successful Response
     * @throws ApiError
     */
    public static createRunConversationsConversationIdRunTriggersPost(
        conversationId: string,
        requestBody: CreateRunRequest,
    ): CancelablePromise<CreateRunResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/conversations/{conversation_id}/run-triggers',
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
     * Create Run
     * @param conversationId
     * @param requestBody
     * @returns CreateRunResponse Successful Response
     * @throws ApiError
     */
    public static createRunConversationsConversationIdRunsPost(
        conversationId: string,
        requestBody: CreateRunRequest,
    ): CancelablePromise<CreateRunResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/conversations/{conversation_id}/runs',
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
     * Get Run
     * @param runId
     * @returns RunSummaryResponse Successful Response
     * @throws ApiError
     */
    public static getRunRunsRunIdGet(
        runId: string,
    ): CancelablePromise<RunSummaryResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/runs/{run_id}',
            path: {
                'run_id': runId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Or Stream Run Events
     * @param runId
     * @param afterEventNumber
     * @param lastEventId
     * @returns RunEventResponse Successful Response
     * @throws ApiError
     */
    public static listOrStreamRunEventsRunsRunIdEventsGet(
        runId: string,
        afterEventNumber?: (number | null),
        lastEventId?: (string | null),
    ): CancelablePromise<Array<RunEventResponse>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/runs/{run_id}/events',
            path: {
                'run_id': runId,
            },
            headers: {
                'Last-Event-ID': lastEventId,
            },
            query: {
                'after_event_number': afterEventNumber,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Cancel Run
     * @param runId
     * @returns RunSummaryResponse Successful Response
     * @throws ApiError
     */
    public static cancelRunRunsRunIdCancelPost(
        runId: string,
    ): CancelablePromise<RunSummaryResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/runs/{run_id}/cancel',
            path: {
                'run_id': runId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Retry Run
     * @param runId
     * @returns RunSummaryResponse Successful Response
     * @throws ApiError
     */
    public static retryRunRunsRunIdRetryPost(
        runId: string,
    ): CancelablePromise<RunSummaryResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/runs/{run_id}/retry',
            path: {
                'run_id': runId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
