"""Conversations domain layer placeholder."""

from researchlens.modules.conversations.domain.chat_intent import (
    IntentDecision,
    classify_chat_intent,
    greeting_response,
    is_greeting,
    is_generic_pipeline_trigger,
    is_substantive_prompt,
    parse_consent_reply,
)
from researchlens.modules.conversations.domain.conversation import (
    Conversation,
    normalize_conversation_title,
)
from researchlens.modules.conversations.domain.message import (
    Message,
    MessageRole,
    MessageType,
    normalize_client_message_id,
)
from researchlens.modules.conversations.domain.run_trigger import (
    RunTrigger,
    RunTriggerStatus,
    normalize_client_request_id,
    normalize_run_trigger_text,
)

__all__ = [
    "Conversation",
    "IntentDecision",
    "Message",
    "MessageRole",
    "MessageType",
    "RunTrigger",
    "RunTriggerStatus",
    "classify_chat_intent",
    "greeting_response",
    "is_generic_pipeline_trigger",
    "is_greeting",
    "is_substantive_prompt",
    "normalize_client_message_id",
    "normalize_client_request_id",
    "normalize_conversation_title",
    "normalize_run_trigger_text",
    "parse_consent_reply",
]
