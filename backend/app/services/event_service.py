from types import SimpleNamespace

from ..core.database import get_database
from ..core.exceptions import CareLoopError
from ..schemas.care_event import CareEventCreate
from .care_action_service import process_action_event, verify_completion
from .handoff_service import acknowledge_handoff, reject_handoff, send_handoff


def _build_action_payload(payload: CareEventCreate):
    return SimpleNamespace(
        event_id=payload.event_id,
        source=payload.source,
        actor_id=getattr(payload.actor, "id", None),
        actor_role=getattr(payload.actor, "role", None),
        occurred_at=payload.occurred_at,
        payload=payload.payload,
    )


def _build_handoff_payload(payload: CareEventCreate):
    return SimpleNamespace(
        event_id=payload.event_id,
        actor_id=getattr(payload.actor, "id", None),
        actor_role=getattr(payload.actor, "role", None),
        occurred_at=payload.occurred_at,
        payload=payload.payload,
    )


def _build_verification_payload(payload: CareEventCreate):
    return SimpleNamespace(
        event_id=payload.event_id,
        evidence_id=payload.payload.get("evidence_id") if isinstance(payload.payload, dict) else None,
        verification_note=payload.payload.get("verification_note", "") if isinstance(payload.payload, dict) else "",
        actor_id=getattr(payload.actor, "id", None),
        actor_role=getattr(payload.actor, "role", None),
    )


def process_event(payload: CareEventCreate) -> dict:
    database = get_database()
    event_id = str(payload.event_id)
    try:
        existing = database.care_events.get(event_id)
        if existing:
            if existing["payload"] != payload.payload:
                raise CareLoopError(
                    "IDEMPOTENCY_CONFLICT",
                    "The event ID was reused with a different payload.",
                    409,
                )
            return existing["result_snapshot"]
        database.care_events[event_id] = {"payload": payload.payload, "result_snapshot": {}}
        if payload.event_type in {"ACTION_STARTED", "COMPLETION_REPORTED"} and payload.action_id:
            result = process_action_event(payload.action_id, payload.event_type, _build_action_payload(payload))
        elif payload.event_type == "COMPLETION_VERIFIED" and payload.action_id:
            result = verify_completion(payload.action_id, _build_verification_payload(payload))
        elif payload.event_type == "HANDOFF_ACKNOWLEDGED" and payload.handoff_id:
            result = acknowledge_handoff(payload.handoff_id, _build_handoff_payload(payload))
        elif payload.event_type == "HANDOFF_SENT" and payload.handoff_id:
            result = send_handoff(payload.handoff_id, _build_handoff_payload(payload))
        elif payload.event_type == "HANDOFF_REJECTED" and payload.handoff_id:
            result = reject_handoff(payload.handoff_id, _build_handoff_payload(payload))
        else:
            result = {"event_id": event_id, "processing_status": "PROCESSED"}
        database.care_events[event_id]["result_snapshot"] = result
        return result
    except CareLoopError:
        raise
    except Exception as exc:  # pragma: no cover - defensive fallback for DB-backed deployments
        raise CareLoopError(
            "INTERNAL_ERROR",
            "The event could not be processed because the database returned an error.",
            500,
        ) from exc
