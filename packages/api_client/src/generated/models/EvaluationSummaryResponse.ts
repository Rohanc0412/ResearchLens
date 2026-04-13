/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type EvaluationSummaryResponse = {
    evaluation_pass_id: string;
    section_count: number;
    evaluated_section_count: number;
    issue_count: number;
    sections_requiring_repair_count: number;
    quality_pct: number;
    unsupported_claim_rate: number;
    pass_rate: number;
    ragas_faithfulness_pct: number;
    issues_by_type: Record<string, number>;
    repair_recommended: boolean;
    sections_requiring_repair: Array<string>;
};

