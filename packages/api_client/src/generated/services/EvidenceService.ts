/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ChunkDetailResponse } from '../models/ChunkDetailResponse';
import type { RunEvidenceSummaryResponse } from '../models/RunEvidenceSummaryResponse';
import type { SectionEvidenceTraceResponse } from '../models/SectionEvidenceTraceResponse';
import type { SourceDetailResponse } from '../models/SourceDetailResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class EvidenceService {
    /**
     * Get Run Evidence
     * @param runId
     * @returns RunEvidenceSummaryResponse Successful Response
     * @throws ApiError
     */
    public static getRunEvidenceRunsRunIdEvidenceGet(
        runId: string,
    ): CancelablePromise<RunEvidenceSummaryResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/runs/{run_id}/evidence',
            path: {
                'run_id': runId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Section Evidence
     * @param runId
     * @param sectionId
     * @returns SectionEvidenceTraceResponse Successful Response
     * @throws ApiError
     */
    public static getSectionEvidenceRunsRunIdEvidenceSectionsSectionIdGet(
        runId: string,
        sectionId: string,
    ): CancelablePromise<SectionEvidenceTraceResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/runs/{run_id}/evidence/sections/{section_id}',
            path: {
                'run_id': runId,
                'section_id': sectionId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Chunk Detail
     * @param chunkId
     * @param contextWindow
     * @returns ChunkDetailResponse Successful Response
     * @throws ApiError
     */
    public static getChunkDetailEvidenceChunksChunkIdGet(
        chunkId: string,
        contextWindow: number = 1,
    ): CancelablePromise<ChunkDetailResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/evidence/chunks/{chunk_id}',
            path: {
                'chunk_id': chunkId,
            },
            query: {
                'context_window': contextWindow,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Source Detail
     * @param sourceId
     * @returns SourceDetailResponse Successful Response
     * @throws ApiError
     */
    public static getSourceDetailEvidenceSourcesSourceIdGet(
        sourceId: string,
    ): CancelablePromise<SourceDetailResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/evidence/sources/{source_id}',
            path: {
                'source_id': sourceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
