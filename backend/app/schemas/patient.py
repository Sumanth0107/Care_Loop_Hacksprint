from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


PlanStatus = Literal["DRAFT", "PENDING_APPROVAL", "APPROVED", "SUPERSEDED", "CANCELLED"]


class Patient(BaseModel):
    id: UUID
    external_ref: str | None = None
    display_name: str
    created_at: datetime


class CarePlanCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_id: UUID
    source_text: str | None = None
    created_by: str = "demo-coordinator"


class CarePlan(BaseModel):
    id: UUID
    patient_id: UUID
    version: int
    status: PlanStatus
    source_text: str | None = None
    created_by: str
    created_at: datetime
    updated_at: datetime


class CareJourneyDependency(BaseModel):
    requirement_type: str
    satisfied: bool


class CareJourneyAction(BaseModel):
    id: UUID
    title: str
    status: str
    responsible_role: str
    dependencies: list[CareJourneyDependency] = Field(default_factory=list)


class CareJourney(BaseModel):
    patient: Patient
    care_plan: CarePlan
    actions: list[CareJourneyAction]
    open_exception_count: int
