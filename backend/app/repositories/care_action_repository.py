```python
from ..core.config import get_settings
from ..core.database import get_database, get_supabase_client


def get_care_action(action_id: str) -> dict | None:
    if not get_settings().supabase_configured:
        db = get_database()
        return db.care_actions.get(action_id) or next(
            (
                item
                for item in db.care_actions.values()
                if item.get("id") == action_id
            ),
            None,
        )

    response = (
        get_supabase_client()
        .table("care_actions")
        .select("*")
        .eq("id", action_id)
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None
```