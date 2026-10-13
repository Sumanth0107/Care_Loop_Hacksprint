```python
from typing import Any

from ..core.config import get_settings
from ..core.database import get_database, get_supabase_client


def insert_audit_entry(entry: dict[str, Any]) -> dict[str, Any]:
    required = (
        "entity_type",
        "entity_id",
        "operation",
        "actor_role",
    )
    missing = [key for key in required if not entry.get(key)]

    if missing:
        raise ValueError(
            f"Missing required audit fields: {', '.join(missing)}"
        )

    allowed = {
        "event_id",
        "entity_type",
        "entity_id",
        "operation",
        "actor_id",
        "actor_role",
        "before_state",
        "after_state",
    }
    payload = {
        key: value
        for key, value in entry.items()
        if key in allowed
    }

    if not get_settings().supabase_configured:
        record = dict(payload)
        get_database().audit_log.append(record)
        return record

    response = (
        get_supabase_client()
        .table("audit_log")
        .insert(payload)
        .execute()
    )

    if not response.data:
        raise RuntimeError("Audit entry insertion returned no record")

    return response.data[0]
```