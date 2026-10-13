from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CareException(BaseModel):
    id: UUID
    exception_type: str
    status: Literal["OPEN", "IN_PROGRESS", "RESOLVED", "DISMISSED"]
    assigned_role: str
    reason: str
    resolution_note: str | None = None
    action_id: UUID | None = None
    handoff_id: UUID | None = None
    created_at: datetime
    resolved_at: datetime | None = None
    resolved_by: str | None = None


class ExceptionPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["IN_PROGRESS", "RESOLVED", "DISMISSED"]
    assigned_role: str | None = None
    resolution_note: str | None = None
    actor_id: str = "demo-coordinator"
