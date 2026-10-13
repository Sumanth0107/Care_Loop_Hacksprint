from ..core.database import get_database
from ..core.exceptions import CareLoopError
from ..schemas.care_event import CareEventCreate
from .care_action_service import process_action_event
from .handoff_service import acknowledge_handoff, send_handoff


def process_event(payload: CareEventCreate) -> dict:
    database = get_database()
    event_id = str(payload.event_id)
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
        action_payload = type(
            "ActionPayload",
            (),
            {
                "event_id": payload.event_id,
                "source": payload.source,
                "actor_id": payload.actor.id,
                "actor_role": payload.actor.role,
                "occurred_at": payload.occurred_at,
                "payload": payload.payload,
            },
        )()
        result = process_action_event(payload.action_id, payload.event_type, action_payload)
    elif payload.event_type == "HANDOFF_ACKNOWLEDGED" and payload.handoff_id:
        result = acknowledge_handoff(payload.handoff_id, payload)
    elif payload.event_type == "HANDOFF_SENT" and payload.handoff_id:
        result = send_handoff(payload.handoff_id, payload)
    else:
        result = {"event_id": event_id, "processing_status": "PROCESSED"}
    database.care_events[event_id]["result_snapshot"] = result
    return result
