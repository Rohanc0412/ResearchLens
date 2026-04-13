/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { EvidenceChunkRefResponse } from './EvidenceChunkRefResponse';
import type { EvidenceClaimTraceResponse } from './EvidenceClaimTraceResponse';
import type { EvidenceIssueTraceResponse } from './EvidenceIssueTraceResponse';
import type { EvidenceSourceRefResponse } from './EvidenceSourceRefResponse';
export type SectionEvidenceTraceResponse = {
    section_id: string;
    section_title: string;
    section_order: number;
    canonical_text: string;
    canonical_summary: string;
    repaired: boolean;
    latest_evaluation_result_id: (string | null);
    repair_result_id: (string | null);
    claims: Array<EvidenceClaimTraceResponse>;
    issues: Array<EvidenceIssueTraceResponse>;
    evidence_chunks: Array<EvidenceChunkRefResponse>;
    source_refs: Array<EvidenceSourceRefResponse>;
    unresolved_quality_findings: Array<EvidenceIssueTraceResponse>;
};

