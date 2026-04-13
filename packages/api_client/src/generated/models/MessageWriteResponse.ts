/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type MessageWriteResponse = {
    id: string;
    tenant_id: string;
    conversation_id: string;
    role: string;
    type: string;
    content_text: (string | null);
    content_json: (Record<string, any> | null);
    metadata_json: (Record<string, any> | null);
    created_at: string;
    client_message_id: (string | null);
    idempotent_replay: boolean;
};

