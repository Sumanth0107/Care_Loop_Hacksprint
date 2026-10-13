from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class JourneyPatient(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: UUID
    external_ref: str
    display_name: str


class JourneyCarePlan(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: UUID
    patient_id: UUID
    version: int
    status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class JourneyDependency(BaseModel):
    requirement_type: str
    satisfied: bool


class JourneyAction(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: UUID
    care_plan_id: UUID
    title: str
    status: str
    due_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    dependencies: list[JourneyDependency] = Field(default_factory=list)


class JourneyHandoff(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: UUID
    action_id: UUID
    status: str
    recipient_role: str | None = None
    recipient_id: str | None = None
    deadline_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class JourneyException(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: UUID
    status: str
    action_id: UUID | None = None
    handoff_id: UUID | None = None
    assigned_role: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CareJourneyData(BaseModel):
    patient: JourneyPatient
    care_plan: JourneyCarePlan
    actions: list[JourneyAction]
    handoffs: list[JourneyHandoff]
    active_exceptions: list[JourneyException]
    open_exception_count: int


class CareJourneyEnvelope(BaseModel):
    success: bool
    data: CareJourneyData
    meta: dict[str, Any]
    error: Any | None = None
