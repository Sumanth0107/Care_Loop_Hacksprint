from uuid import UUID

from ..core.database import get_database


def record_audit(entity_type: str, entity_id: str, operation: str, actor_id: str | None, actor_role: str, before: dict | None, after: dict | None, event_id: str | None = None) -> None:
    from datetime import UTC, datetime
    from uuid import uuid4

    get_database().audit_log.append(
        {
            "id": str(uuid4()),
            "event_id": event_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "operation": operation,
            "actor_id": actor_id,
            "actor_role": actor_role,
            "before_state": before,
            "after_state": after,
            "created_at": datetime.now(UTC),
        }
    )


def list_audit(entity_type: str | None = None, entity_id: UUID | None = None) -> list[dict]:
    return [
        item
        for item in get_database().audit_log
        if (entity_type is None or item["entity_type"] == entity_type)
        and (entity_id is None or item["entity_id"] == str(entity_id))
    ]
