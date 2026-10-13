from datetime import UTC, datetime
from uuid import UUID

from ..core.database import get_database
from ..schemas.care_action import ActionEventRequest, VerifyCompletionRequest
from .audit_service import record_audit
from .state_machine import transition


def _resolve_actor(payload: object) -> tuple[str | None, str | None]:
    actor = getattr(payload, "actor", None)
    if actor is not None:
        return getattr(actor, "id", None), getattr(actor, "role", None)
    return getattr(payload, "actor_id", None), getattr(payload, "actor_role", None)


def get_action(action_id: UUID) -> dict:
    action = get_database().care_actions.get(str(action_id))
    if action is None:
        raise KeyError(f"Care action '{action_id}' does not exist.")
    return action


def process_action_event(action_id: UUID, event_type: str, payload: ActionEventRequest) -> dict:
    action = get_action(action_id)
    before = action.copy()
    actor_id, actor_role = _resolve_actor(payload)
    target = "IN_PROGRESS" if event_type == "ACTION_STARTED" else "AWAITING_VERIFICATION"
    action["status"] = transition(action["status"], target)
    if event_type == "COMPLETION_REPORTED":
        action["completion_reported_at"] = payload.occurred_at
    action["updated_at"] = datetime.now(UTC)
    record_audit(
        "care_action",
        action["id"],
        "STATUS_CHANGED",
        actor_id,
        actor_role or "SYSTEM",
        before,
        action,
        str(payload.event_id),
    )
    return {
        "event_id": str(payload.event_id),
        "processing_status": "PROCESSED",
        "action": action,
        "affected_exception_ids": [],
    }


def verify_completion(action_id: UUID, payload: VerifyCompletionRequest) -> dict:
    action = get_action(action_id)
    before = action.copy()
    actor_id, actor_role = _resolve_actor(payload)
    action["status"] = transition(action["status"], "VERIFIED_COMPLETE")
    action["verified_at"] = datetime.now(UTC)
    action["verified_by"] = actor_id or "demo-coordinator"
    action["updated_at"] = datetime.now(UTC)
    record_audit(
        "care_action",
        action["id"],
        "STATUS_CHANGED",
        actor_id or "demo-coordinator",
        actor_role or "CARE_COORDINATOR",
        before,
        action,
        str(payload.event_id),
    )
    return {"event_id": str(payload.event_id), "processing_status": "PROCESSED", "action": action}
