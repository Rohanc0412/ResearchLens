/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type EvidenceClaimTraceResponse = {
    claim_id: string;
    claim_index: number;
    claim_text: string;
    verdict: (string | null);
    cited_chunk_ids: Array<string>;
    supported_chunk_ids: Array<string>;
    allowed_chunk_ids: Array<string>;
    issue_ids: Array<string>;
};

