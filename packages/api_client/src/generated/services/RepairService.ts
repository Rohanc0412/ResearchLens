/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { RepairSectionResponse } from '../models/RepairSectionResponse';
import type { RepairSummaryResponse } from '../models/RepairSummaryResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class RepairService {
    /**
     * Get Run Repair
     * @param runId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getRunRepairRunsRunIdRepairGet(
        runId: string,
    ): CancelablePromise<(RepairSummaryResponse | null)> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/runs/{run_id}/repair',
            path: {
                'run_id': runId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Run Repair Sections
     * @param runId
     * @returns RepairSectionResponse Successful Response
     * @throws ApiError
     */
    public static listRunRepairSectionsRunsRunIdRepairSectionsGet(
        runId: string,
    ): CancelablePromise<Array<RepairSectionResponse>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/runs/{run_id}/repair/sections',
            path: {
                'run_id': runId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
