/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type RunSummaryResponse = {
    id: string;
    project_id: string;
    conversation_id: (string | null);
    status: string;
    current_stage: (string | null);
    output_type: string;
    client_request_id: (string | null);
    retry_count: number;
    cancel_requested: boolean;
    created_at: string;
    updated_at: string;
    started_at: (string | null);
    finished_at: (string | null);
    failure_reason: (string | null);
    error_code: (string | null);
    last_event_number: number;
    display_status: string;
    display_stage: string;
    can_stop: boolean;
    can_retry: boolean;
};

