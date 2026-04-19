from contextlib import AbstractAsyncContextManager
from typing import Any
from typing import Protocol
from uuid import UUID

from researchlens.modules.conversations.application.cursor import ConversationListCursor
from researchlens.modules.conversations.domain import Conversation, Message, RunTrigger


class ProjectScopeReader(Protocol):
    async def project_exists_for_tenant(
        self,
        *,
        tenant_id: UUID,
        project_id: UUID,
    ) -> bool: ...


class ConversationRepository(Protocol):
    async def add(self, conversation: Conversation) -> Conversation: ...

    async def get_by_id_for_tenant(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
    ) -> Conversation | None: ...

    async def list_by_project(
        self,
        *,
        tenant_id: UUID,
        project_id: UUID,
        limit: int,
        cursor: ConversationListCursor | None,
    ) -> list[Conversation]: ...

    async def save(self, conversation: Conversation) -> Conversation | None: ...

    async def delete_by_id_for_tenant(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
    ) -> bool: ...


class MessageRepository(Protocol):
    async def add(self, message: Message) -> Message: ...

    async def update_metadata(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        message_id: UUID,
        metadata_json: dict[str, Any] | None,
    ) -> Message | None: ...

    async def get_by_id_for_tenant(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        message_id: UUID,
    ) -> Message | None: ...

    async def get_by_client_message_id(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        client_message_id: str,
    ) -> Message | None: ...

    async def list_by_conversation(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
    ) -> list[Message]: ...

    async def list_recent_chat(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        limit: int,
        exclude_message_id: UUID | None = None,
    ) -> list[Message]: ...


class RunTriggerRepository(Protocol):
    async def add(self, trigger: RunTrigger) -> RunTrigger: ...


class TransactionManager(Protocol):
    def boundary(self) -> AbstractAsyncContextManager[None]: ...
