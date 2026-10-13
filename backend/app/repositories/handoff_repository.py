```python
from ..core.config import get_settings
from ..core.database import get_database, get_supabase_client


def get_handoff(handoff_id: str) -> dict | None:
    if not get_settings().supabase_configured:
        db = get_database()
        return db.handoffs.get(handoff_id) or next(
            (
                item
                for item in db.handoffs.values()
                if item.get("id") == handoff_id
            ),
            None,
        )

    response = (
        get_supabase_client()
        .table("handoffs")
        .select("*")
        .eq("id", handoff_id)
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None
```