from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ActorReference(BaseModel):
    id: str | None = None
    role: str


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
        if actor is not None:
            if actor.role:
                return self
        if self.actor_role:
            return self
        raise ValueError("Either actor.role or actor_role must be provided.")


class VerifyCompletionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: UUID
    evidence_id: UUID
    verification_note: str
    actor: ActorReference | None = None
    actor_id: str | None = None
    actor_role: str | None = None

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
