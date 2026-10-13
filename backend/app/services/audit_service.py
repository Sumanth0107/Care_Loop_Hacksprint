from datetime import UTC, datetime
from uuid import UUID, uuid4

from ..core.database import get_database
from ..repositories.audit_repository import list_audit_entries


def record_audit(entity_type: str, entity_id: str, operation: str, actor_id: str | None, actor_role: str, before: dict | None, after: dict | None, event_id: str | None = None) -> None:
    entry = {
        "event_id": event_id,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "operation": operation,
        "actor_id": actor_id,
        "actor_role": actor_role,
        "before_state": before,
        "after_state": after,
    }
    get_database().audit_log.append(
        {
            "id": str(uuid4()),
            **entry,
            "created_at": datetime.now(UTC),
        }
    )


def list_audit(entity_type: str | None = None, entity_id: UUID | None = None) -> list[dict]:
    return list_audit_entries(
        entity_type,
        str(entity_id) if entity_id is not None else None,
    )
