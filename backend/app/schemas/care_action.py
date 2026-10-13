from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


ActionStatus = Literal[
    "PENDING",
    "READY",
    "IN_PROGRESS",
    "AWAITING_VERIFICATION",
    "VERIFIED_COMPLETE",
    "BLOCKED",
    "CANCELLED",
]


class CareAction(BaseModel):
    id: UUID
    care_plan_id: UUID
    title: str
    description: str | None = None
    action_type: str
    status: ActionStatus
    responsible_role: str
    due_at: datetime | None = None
    completion_reported_at: datetime | None = None
    verified_at: datetime | None = None
    verified_by: str | None = None
    created_at: datetime
    updated_at: datetime


class ActionEventRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: UUID
    source: str
    actor_id: str | None = None
    actor_role: str
    occurred_at: datetime
    payload: dict = Field(default_factory=dict)


class VerifyCompletionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: UUID
    evidence_id: UUID
    verification_note: str
    actor_id: str = "demo-coordinator"
    actor_role: str = "CARE_COORDINATOR"
