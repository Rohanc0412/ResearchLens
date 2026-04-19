/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type RunEventResponse = {
    run_id: string;
    event_number: number;
    event_type: string;
    audience: string;
    level: string;
    status: string;
    stage: (string | null);
    display_status: string;
    display_stage: string;
    message: string;
    retry_count: number;
    cancel_requested: boolean;
    payload: (Record<string, any> | null);
    ts: string;
};

