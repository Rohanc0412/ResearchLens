/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { EvidenceSectionSummaryResponse } from './EvidenceSectionSummaryResponse';
export type RunEvidenceSummaryResponse = {
    run_id: string;
    project_id: string;
    conversation_id: (string | null);
    section_count: number;
    source_count: number;
    chunk_count: number;
    claim_count: number;
    issue_count: number;
    repaired_section_count: number;
    unresolved_section_count: number;
    latest_evaluation_pass_id: (string | null);
    latest_repair_pass_id: (string | null);
    artifact_count: number;
    sections: Array<EvidenceSectionSummaryResponse>;
};

