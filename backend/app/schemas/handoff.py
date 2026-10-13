from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ActorReference(BaseModel):
    id: str | None = None
    role: str


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
    actor: ActorReference | None = None
    actor_id: str | None = None
    actor_role: str | None = None
    occurred_at: datetime
    payload: dict = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def normalize_actor_fields(cls, values):
        if not isinstance(values, dict):
            return values
        actor = values.get("actor")
        if isinstance(actor, dict):
            values.setdefault("actor_id", actor.get("id"))
            values.setdefault("actor_role", actor.get("role"))
        return values

    @model_validator(mode="after")
    def ensure_actor_reference(self):
        actor = self.actor
        if actor is not None and actor.role:
            return self
        if self.actor_role:
            return self
        raise ValueError("Either actor.role or actor_role must be provided.")
