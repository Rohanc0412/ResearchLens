/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type EvaluationIssueResponse = {
    issue_id: string;
    run_id: string;
    evaluation_pass_id: string;
    section_id: string;
    section_title: string;
    section_order: number;
    claim_id: (string | null);
    claim_index: (number | null);
    claim_text: (string | null);
    verdict: (string | null);
    issue_type: string;
    severity: string;
    message: string;
    rationale: string;
    cited_chunk_ids: Array<string>;
    supported_chunk_ids: Array<string>;
    allowed_chunk_ids: Array<string>;
    repair_hint: string;
    created_at: string;
};

