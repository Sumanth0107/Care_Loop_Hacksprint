from datetime import UTC, datetime
from uuid import UUID, uuid4

from ..core.database import get_database
from ..core.exceptions import CareLoopError
from ..schemas.handoff import HandoffCreate, HandoffEventRequest
from .audit_service import record_audit
from .dependency_service import refresh_action_statuses


def _resolve_actor(payload: object) -> tuple[str | None, str | None]:
    actor = getattr(payload, "actor", None)
    if actor is not None:
        return getattr(actor, "id", None), getattr(actor, "role", None)
    return getattr(payload, "actor_id", None), getattr(payload, "actor_role", None)


def create_handoff(payload: HandoffCreate) -> dict:
    database = get_database()
    if str(payload.action_id) not in database.care_actions:
        raise KeyError(f"Care action '{payload.action_id}' does not exist.")
    now = datetime.now(UTC)
    handoff = {
        "id": str(uuid4()),
        "action_id": str(payload.action_id),
        "recipient_role": payload.recipient_role,
        "recipient_id": payload.recipient_id,
        "status": "PENDING",
        "sent_at": None,
        "acknowledged_at": None,
        "acknowledged_by": None,
        "deadline_at": payload.deadline_at,
        "rejection_reason": None,
        "created_at": now,
    }
    database.handoffs[handoff["id"]] = handoff
    return handoff


def _get_handoff(handoff_id: UUID) -> dict:
    handoff = get_database().handoffs.get(str(handoff_id))
    if handoff is None:
        raise KeyError(f"Handoff '{handoff_id}' does not exist.")
    return handoff


def send_handoff(handoff_id: UUID, payload: HandoffEventRequest) -> dict:
    handoff = _get_handoff(handoff_id)
    if handoff["status"] != "PENDING":
        raise CareLoopError("INVALID_STATE_TRANSITION", "Only pending handoffs can be sent.", 409)
    before = handoff.copy()
    actor_id, actor_role = _resolve_actor(payload)
    handoff["status"] = "SENT"
    handoff["sent_at"] = payload.occurred_at
    record_audit("handoff", handoff["id"], "STATUS_CHANGED", actor_id, actor_role or "SYSTEM", before, handoff, str(payload.event_id))
    return handoff


def acknowledge_handoff(handoff_id: UUID, payload: HandoffEventRequest) -> dict:
    handoff = _get_handoff(handoff_id)
    if handoff["status"] != "SENT":
        raise CareLoopError("INVALID_STATE_TRANSITION", "Only sent handoffs can be acknowledged.", 409)
    before = handoff.copy()
    actor_id, actor_role = _resolve_actor(payload)
    handoff["status"] = "ACKNOWLEDGED"
    handoff["acknowledged_at"] = payload.occurred_at
    handoff["acknowledged_by"] = actor_id
    record_audit("handoff", handoff["id"], "ACKNOWLEDGED", actor_id, actor_role or "SYSTEM", before, handoff, str(payload.event_id))
    refresh_action_statuses()
    return handoff


def reject_handoff(handoff_id: UUID, payload: HandoffEventRequest) -> dict:
    handoff = _get_handoff(handoff_id)
    if handoff["status"] != "SENT":
        raise CareLoopError("INVALID_STATE_TRANSITION", "Only sent handoffs can be rejected.", 409)
    before = handoff.copy()
    actor_id, actor_role = _resolve_actor(payload)
    handoff["status"] = "REJECTED"
    handoff["rejection_reason"] = payload.payload.get("reason") or "Rejected by recipient."
    record_audit("handoff", handoff["id"], "REJECTED", actor_id, actor_role or "SYSTEM", before, handoff, str(payload.event_id))
    return handoff
