from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class Handoff(BaseModel):
    id: UUID
    action_id: UUID
    recipient_role: str
    recipient_id: str | None = None
    status: Literal["PENDING", "SENT", "ACKNOWLEDGED", "REJECTED", "CANCELLED"]
    sent_at: datetime | None = None
    acknowledged_at: datetime | None = None
    acknowledged_by: str | None = None
    deadline_at: datetime
    rejection_reason: str | None = None
    created_at: datetime


class HandoffCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action_id: UUID
    recipient_role: str
    recipient_id: str | None = None
    deadline_at: datetime


class HandoffEventRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: UUID
    actor_id: str | None = None
    actor_role: str
    occurred_at: datetime
    payload: dict = {}
