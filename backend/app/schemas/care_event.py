from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


EventType = Literal[
    "ACTION_STARTED",
    "COMPLETION_REPORTED",
    "COMPLETION_VERIFIED",
    "HANDOFF_SENT",
    "HANDOFF_ACKNOWLEDGED",
    "HANDOFF_REJECTED",
    "BARRIER_REPORTED",
    "RESCHEDULE_REQUESTED",
]
EventSource = Literal["PATIENT", "DEPARTMENT", "CARE_COORDINATOR", "DEPARTMENT_SIMULATOR", "SYSTEM"]


class Actor(BaseModel):
    id: str | None = None
    role: str


class CareEventCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: UUID
    event_type: EventType
    action_id: UUID | None = None
    handoff_id: UUID | None = None
    source: EventSource
    actor: Actor
    occurred_at: datetime
    payload: dict[str, Any] = Field(default_factory=dict)
