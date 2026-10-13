```python
from ..core.config import get_settings
from ..core.database import get_database, get_supabase_client


def get_active_exceptions() -> list[dict]:
    active_statuses = {"OPEN", "IN_PROGRESS"}

    if not get_settings().supabase_configured:
        return [
            item
            for item in get_database().exceptions.values()
            if item.get("status") in active_statuses
        ]

    response = (
        get_supabase_client()
        .table("exceptions")
        .select("*")
        .in_("status", ["OPEN", "IN_PROGRESS"])
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []
```