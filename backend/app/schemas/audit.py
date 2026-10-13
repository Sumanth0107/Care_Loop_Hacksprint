from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class AuditEntry(BaseModel):
    id: UUID
    event_id: UUID | None = None
    entity_type: str
    entity_id: UUID
    operation: str
    actor_id: str | None = None
    actor_role: str
    before_state: dict[str, Any] | None = None
    after_state: dict[str, Any] | None = None
    created_at: datetime
