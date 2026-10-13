from datetime import UTC, datetime
from uuid import UUID

from ..core.database import get_database
from ..core.exceptions import CareLoopError
from ..schemas.exception import ExceptionPatch
from .audit_service import record_audit


def list_exceptions(status: str | None, assigned_role: str | None, limit: int) -> list[dict]:
    items = list(get_database().exceptions.values())
    if status:
        items = [item for item in items if item["status"] == status]
    if assigned_role:
        items = [item for item in items if item["assigned_role"] == assigned_role]
    return items[:limit]


def update_exception(exception_id: UUID, payload: ExceptionPatch) -> dict:
    database = get_database()
    exception = database.exceptions.get(str(exception_id))
    if exception is None:
        raise CareLoopError("RESOURCE_NOT_FOUND", f"Exception '{exception_id}' does not exist.", 404)
    allowed = {
        "OPEN": {"IN_PROGRESS", "RESOLVED", "DISMISSED"},
        "IN_PROGRESS": {"RESOLVED", "DISMISSED"},
    }
    if payload.status not in allowed.get(exception["status"], set()):
        raise CareLoopError("INVALID_STATE_TRANSITION", "The exception transition is not allowed.", 409)
    before = exception.copy()
    exception["status"] = payload.status
    if payload.assigned_role:
        exception["assigned_role"] = payload.assigned_role
    exception["resolution_note"] = payload.resolution_note
    exception["resolved_at"] = datetime.now(UTC) if payload.status in {"RESOLVED", "DISMISSED"} else None
    exception["resolved_by"] = payload.actor_id if payload.status in {"RESOLVED", "DISMISSED"} else None
    record_audit("exception", exception["id"], "STATUS_CHANGED", payload.actor_id, "CARE_COORDINATOR", before, exception)
    return exception
