/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { RepairSectionResponse } from './RepairSectionResponse';
export type RepairSummaryResponse = {
    repair_pass_id: (string | null);
    run_id: string;
    status: string;
    selected_count: number;
    changed_count: number;
    unresolved_count: number;
    sections: Array<RepairSectionResponse>;
};

