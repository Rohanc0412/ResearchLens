from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CreateRunRequest(BaseModel):
    source_message_id: UUID | None = None
    request_text: str
    client_request_id: str | None = None
    output_type: str = "report"

    model_config = ConfigDict(extra="forbid")
