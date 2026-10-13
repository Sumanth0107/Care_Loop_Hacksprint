import base64
import binascii
import json
from datetime import datetime
from uuid import UUID

from ..core.config import get_settings
from ..core.database import get_database, get_supabase_client
from ..core.exceptions import CareLoopError


def _encode_cursor(
    created_at: datetime,
    exception_id: str,
    status: str | None,
    assigned_role: str | None,
) -> str:
    cursor_data = {
        "v": 1,
        "created_at": created_at.isoformat(),
        "id": exception_id,
        "status": status,
        "assigned_role": assigned_role,
    }
    encoded = json.dumps(cursor_data, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(encoded).decode("ascii").rstrip("=")


def _decode_cursor(
    cursor: str,
    status: str | None,
    assigned_role: str | None,
) -> tuple[datetime, str] | None:
    try:
        if not cursor or len(cursor) > 2048:
            raise ValueError
        padding = "=" * (-len(cursor) % 4)
        decoded = base64.b64decode(
            cursor + padding,
            altchars=b"-_",
            validate=True,
        )
        data = json.loads(decoded)
        if (
            not isinstance(data, dict)
            or set(data)
            != {"v", "created_at", "id", "status", "assigned_role"}
            or type(data["v"]) is not int
            or data["v"] != 1
            or not isinstance(data["created_at"], str)
            or not isinstance(data["id"], str)
            or data["status"] != status
            or data["assigned_role"] != assigned_role
        ):
            raise ValueError
        created_at = datetime.fromisoformat(data["created_at"])
        if created_at.tzinfo is None:
            raise ValueError
        exception_id = str(UUID(data["id"]))
        return created_at, exception_id
    except (
        binascii.Error,
        KeyError,
        TypeError,
        UnicodeDecodeError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        raise CareLoopError(
            "INVALID_CURSOR",
            "The exception cursor is invalid or does not match the selected filters.",
            400,
        ) from exc


def _as_datetime(value: datetime | str) -> datetime:
    parsed = value if isinstance(value, datetime) else datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("Exception created_at must include a timezone.")
    return parsed


def list_exceptions(
    status: str | None,
    assigned_role: str | None,
    limit: int,
    cursor: str | None = None,
) -> tuple[list[dict], str | None]:
    boundary = (
        _decode_cursor(cursor, status, assigned_role) if cursor is not None else None
    )
    if not get_settings().supabase_configured:
        items = list(get_database().exceptions.values())
        if status is not None:
            items = [item for item in items if item.get("status") == status]
        if assigned_role is not None:
            items = [
                item for item in items
                if item.get("assigned_role") == assigned_role
            ]
        items.sort(
            key=lambda item: (
                _as_datetime(item["created_at"]),
                str(UUID(item["id"])),
            ),
            reverse=True,
        )
        if boundary is not None:
            items = [
                item
                for item in items
                if (
                    _as_datetime(item["created_at"]),
                    str(UUID(item["id"])),
                )
                < boundary
            ]
        page = items[: limit + 1]
    else:
        query = get_supabase_client().table("exceptions").select("*")
        if status is not None:
            query = query.eq("status", status)
        if assigned_role is not None:
            query = query.eq("assigned_role", assigned_role)
        if boundary is not None:
            created_at, exception_id = boundary
            timestamp = created_at.isoformat()
            query = query.or_(
                f"created_at.lt.{timestamp},"
                f"and(created_at.eq.{timestamp},id.lt.{exception_id})"
            )
        response = (
            query.order("created_at", desc=True)
            .order("id", desc=True)
            .limit(limit + 1)
            .execute()
        )
        page = response.data or []

    has_more = len(page) > limit
    items = page[:limit]
    next_cursor = None
    if has_more and items:
        last_item = items[-1]
        next_cursor = _encode_cursor(
            _as_datetime(last_item["created_at"]),
            str(UUID(last_item["id"])),
            status,
            assigned_role,
        )
    return items, next_cursor


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