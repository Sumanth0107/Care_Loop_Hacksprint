```python
from ..core.config import get_settings
from ..core.database import get_database, get_supabase_client


def get_event_by_id(event_id: str) -> dict | None:
    """Look up the unique care_events.event_id field."""

    if not get_settings().supabase_configured:
        db = get_database()
        return db.care_events.get(event_id) or next(
            (
                item
                for item in db.care_events.values()
                if item.get("event_id") == event_id
            ),
            None,
        )

    response = (
        get_supabase_client()
        .table("care_events")
        .select("*")
        .eq("event_id", event_id)
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None
```