from researchlens.modules.conversations.domain import (
    Conversation,
    Message,
    MessageRole,
    MessageType,
    RunTrigger,
    RunTriggerStatus,
)
from researchlens.modules.conversations.infrastructure.rows.conversation_row import (
    ConversationRow,
)
from researchlens.modules.conversations.infrastructure.rows.message_row import MessageRow
from researchlens.modules.conversations.infrastructure.rows.run_trigger_row import RunTriggerRow


def to_conversation_domain(row: ConversationRow) -> Conversation:
    return Conversation(
        id=row.id,
        tenant_id=row.tenant_id,
        project_id=row.project_id,
        created_by_user_id=row.created_by_user_id,
        title=row.title,
        created_at=row.created_at,
        updated_at=row.updated_at,
        last_message_at=row.last_message_at,
    )


def update_conversation_row(row: ConversationRow, conversation: Conversation) -> None:
    row.project_id = conversation.project_id
    row.title = conversation.title
    row.updated_at = conversation.updated_at
    row.last_message_at = conversation.last_message_at


def to_message_domain(row: MessageRow) -> Message:
    return Message(
        id=row.id,
        tenant_id=row.tenant_id,
        conversation_id=row.conversation_id,
        role=MessageRole(row.role),
        type=MessageType(row.type),
        content_text=row.content_text,
        content_json=row.content_json,
        metadata_json=row.metadata_json,
        created_at=row.created_at,
        client_message_id=row.client_message_id,
    )


def to_run_trigger_domain(row: RunTriggerRow) -> RunTrigger:
    return RunTrigger(
        id=row.id,
        tenant_id=row.tenant_id,
        conversation_id=row.conversation_id,
        project_id=row.project_id,
        source_message_id=row.source_message_id,
        request_text=row.request_text,
        client_request_id=row.client_request_id,
        status=RunTriggerStatus(row.status),
        created_by_user_id=row.created_by_user_id,
        created_at=row.created_at,
    )
