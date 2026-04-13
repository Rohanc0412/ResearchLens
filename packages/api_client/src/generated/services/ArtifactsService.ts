/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ArtifactResponse } from '../models/ArtifactResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class ArtifactsService {
    /**
     * List Run Artifacts
     * @param runId
     * @returns ArtifactResponse Successful Response
     * @throws ApiError
     */
    public static listRunArtifactsRunsRunIdArtifactsGet(
        runId: string,
    ): CancelablePromise<Array<ArtifactResponse>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/runs/{run_id}/artifacts',
            path: {
                'run_id': runId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Artifact
     * @param artifactId
     * @returns ArtifactResponse Successful Response
     * @throws ApiError
     */
    public static getArtifactArtifactsArtifactIdGet(
        artifactId: string,
    ): CancelablePromise<ArtifactResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/artifacts/{artifact_id}',
            path: {
                'artifact_id': artifactId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Download Artifact
     * @param artifactId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static downloadArtifactArtifactsArtifactIdDownloadGet(
        artifactId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/artifacts/{artifact_id}/download',
            path: {
                'artifact_id': artifactId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
