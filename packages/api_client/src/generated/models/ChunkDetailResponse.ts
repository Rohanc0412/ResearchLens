/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { EvidenceChunkRefResponse } from './EvidenceChunkRefResponse';
export type ChunkDetailResponse = {
    chunk_id: string;
    source_id: string;
    source_title: (string | null);
    source_url: (string | null);
    identifiers: Record<string, any>;
    chunk_text: string;
    chunk_index: number;
    context_chunks: Array<EvidenceChunkRefResponse>;
    run_ids: Array<string>;
    section_ids: Array<string>;
};

