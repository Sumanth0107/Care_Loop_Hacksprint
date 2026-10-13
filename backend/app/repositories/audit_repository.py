from typing import Any

from fastapi.encoders import jsonable_encoder

from ..core.config import get_settings
from ..core.database import get_database, get_supabase_client


def list_audit_entries(
    entity_type: str | None,
    entity_id: str | None,
) -> list[dict[str, Any]]:
    if not get_settings().supabase_configured:
        entries = get_database().audit_log
        if entity_type is not None:
            entries = [
                item for item in entries
                if item.get("entity_type") == entity_type
            ]
        if entity_id is not None:
            entries = [
                item for item in entries
                if str(item.get("entity_id")) == entity_id
            ]
        return list(entries)

    query = get_supabase_client().table("audit_log").select("*")
    if entity_type is not None:
        query = query.eq("entity_type", entity_type)
    if entity_id is not None:
        query = query.eq("entity_id", entity_id)
    response = query.order("created_at", desc=True).execute()
    return response.data or []


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
    payload = jsonable_encoder(payload)

    if not get_settings().supabase_configured:
        record = dict(payload)
        get_database().audit_log.append(record)
        return record

    client = get_supabase_client()
    event_id = payload.get("event_id")
    if event_id is not None:
        event_response = (
            client.table("care_events")
            .select("id")
            .eq("event_id", event_id)
            .limit(1)
            .execute()
        )
        if not event_response.data:
            raise ValueError(
                f"Care event '{event_id}' does not exist; audit entry was not written."
            )
        payload["event_id"] = event_response.data[0]["id"]

    response = client.table("audit_log").insert(payload).execute()

    if not response.data:
        raise RuntimeError("Audit entry insertion returned no record")

    return response.data[0]