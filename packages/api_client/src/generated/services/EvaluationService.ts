/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { EvaluationIssueResponse } from '../models/EvaluationIssueResponse';
import type { EvaluationSummaryResponse } from '../models/EvaluationSummaryResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class EvaluationService {
    /**
     * Get Run Evaluation
     * @param runId
     * @returns EvaluationSummaryResponse Successful Response
     * @throws ApiError
     */
    public static getRunEvaluationRunsRunIdEvaluationGet(
        runId: string,
    ): CancelablePromise<EvaluationSummaryResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/runs/{run_id}/evaluation',
            path: {
                'run_id': runId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Run Evaluation Issues
     * @param runId
     * @param sectionId
     * @returns EvaluationIssueResponse Successful Response
     * @throws ApiError
     */
    public static listRunEvaluationIssuesRunsRunIdEvaluationIssuesGet(
        runId: string,
        sectionId?: (string | null),
    ): CancelablePromise<Array<EvaluationIssueResponse>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/runs/{run_id}/evaluation/issues',
            path: {
                'run_id': runId,
            },
            query: {
                'section_id': sectionId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
