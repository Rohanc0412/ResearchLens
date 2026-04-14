from typing import Any


def schema_by_name() -> dict[str, dict[str, Any]]:
    string = {"type": "string", "minLength": 1}
    uuid_string = {"type": "string", "format": "uuid"}
    string_array = {"type": "array", "items": {"type": "string"}}
    uuid_array = {"type": "array", "items": uuid_string}
    return {
        "drafting_section": {
            "type": "object",
            "properties": {
                "section_id": string,
                "section_text": string,
                "section_summary": string,
                "status": {"type": "string", "enum": ["completed"]},
            },
            "required": ["section_id", "section_text", "section_summary", "status"],
            "additionalProperties": False,
        },
        "repair_section": {
            "type": "object",
            "properties": {
                "section_id": string,
                "revised_text": string,
                "revised_summary": string,
                "addressed_issue_ids": uuid_array,
                "citations_used": uuid_array,
                "self_check": string,
            },
            "required": [
                "section_id",
                "revised_text",
                "revised_summary",
                "addressed_issue_ids",
                "citations_used",
                "self_check",
            ],
            "additionalProperties": False,
        },
        "retrieval_query_plan": _retrieval_query_plan_schema(string),
        "retrieval_outline": _retrieval_outline_schema(string, string_array),
        "evaluation_claim_verdicts": _evaluation_claim_verdicts_schema(string, uuid_array),
    }


def _retrieval_query_plan_schema(string: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "queries": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "intent": string,
                        "query": string,
                        "target_section": {"type": ["string", "null"]},
                    },
                    "required": ["intent", "query", "target_section"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["queries"],
        "additionalProperties": False,
    }


def _retrieval_outline_schema(
    string: dict[str, Any],
    string_array: dict[str, Any],
) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "report_title": string,
            "sections": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "section_id": string,
                        "title": string,
                        "goal": string,
                        "suggested_evidence_themes": string_array,
                        "key_points": string_array,
                        "section_order": {"type": "integer", "minimum": 1},
                    },
                    "required": [
                        "section_id",
                        "title",
                        "goal",
                        "suggested_evidence_themes",
                        "key_points",
                        "section_order",
                    ],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["report_title", "sections"],
        "additionalProperties": False,
    }


def _evaluation_claim_verdicts_schema(
    string: dict[str, Any],
    uuid_array: dict[str, Any],
) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "claims": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "claim_index": {"type": "integer", "minimum": 1},
                        "claim_text": string,
                        "verdict": {
                            "type": "string",
                            "enum": [
                                "supported",
                                "missing_citation",
                                "invalid_citation",
                                "overstated",
                                "unsupported",
                                "contradicted",
                            ],
                        },
                        "cited_chunk_ids": uuid_array,
                        "supported_chunk_ids": uuid_array,
                        "rationale": string,
                        "repair_hint": string,
                    },
                    "required": [
                        "claim_index",
                        "claim_text",
                        "verdict",
                        "cited_chunk_ids",
                        "supported_chunk_ids",
                        "rationale",
                        "repair_hint",
                    ],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["claims"],
        "additionalProperties": False,
    }
