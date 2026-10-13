from dataclasses import dataclass, field
from typing import Any

from .config import Settings, get_settings


@dataclass
class InMemoryDatabase:
    """Deterministic development store used until Supabase credentials are configured."""

    patients: dict[str, dict[str, Any]] = field(default_factory=dict)
    care_plans: dict[str, dict[str, Any]] = field(default_factory=dict)
    care_actions: dict[str, dict[str, Any]] = field(default_factory=dict)
    dependencies: list[dict[str, Any]] = field(default_factory=list)
    handoffs: dict[str, dict[str, Any]] = field(default_factory=dict)
    care_events: dict[str, dict[str, Any]] = field(default_factory=dict)
    exceptions: dict[str, dict[str, Any]] = field(default_factory=dict)
    audit_log: list[dict[str, Any]] = field(default_factory=list)


_database = InMemoryDatabase()
_supabase_client: Any | None = None


def get_database() -> InMemoryDatabase:
    return _database


def reset_database() -> InMemoryDatabase:
    global _database
    _database = InMemoryDatabase()
    return _database


def get_supabase_client(settings: Settings | None = None) -> Any | None:
    global _supabase_client
    settings = settings or get_settings()
    if not settings.supabase_configured:
        return None
    if _supabase_client is None:
        from supabase import create_client

        _supabase_client = create_client(settings.supabase_url, settings.supabase_key)
    return _supabase_client



def database_status(settings: Settings | None = None) -> dict[str, Any]:
    settings = settings or get_settings()

    if not settings.supabase_configured:
        return {
            "provider": "supabase",
            "configured": False,
            "connected": False,
            "mode": "in_memory",
        }

    try:
        client = get_supabase_client(settings)

        if client is None:
            raise RuntimeError("Supabase client could not be initialized.")

        # Execute a lightweight database query to verify connectivity.
        client.table("patients").select("id").limit(1).execute()

        return {
            "provider": "supabase",
            "configured": True,
            "connected": True,
            "mode": "supabase",
        }

    except Exception as exc:
        return {
            "provider": "supabase",
            "configured": True,
            "connected": False,
            "mode": "supabase",
            "error": str(exc),
        }

