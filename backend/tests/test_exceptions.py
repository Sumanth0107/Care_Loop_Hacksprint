from datetime import UTC, datetime
import base64
import json
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_database
from app.core.exceptions import CareLoopError
from app.main import app


def test_exception_schema_is_available() -> None:
    from app.schemas.exception import ExceptionPatch

    assert "status" in ExceptionPatch.model_fields


def test_exception_list_filters_all_canonical_statuses(monkeypatch) -> None:
    from app.repositories import exception_repository

    monkeypatch.setattr(
        exception_repository,
        "get_settings",
        lambda: SimpleNamespace(supabase_configured=False),
    )
    now = datetime.now(UTC)
    statuses = ("OPEN", "IN_PROGRESS", "RESOLVED", "DISMISSED")
    database = get_database()
    for status in statuses:
        exception_id = str(uuid4())
        database.exceptions[exception_id] = {
            "id": exception_id,
            "action_id": None,
            "handoff_id": None,
            "exception_type": "HANDOFF_OVERDUE",
            "status": status,
            "assigned_role": "CARDIOLOGY",
            "reason": f"{status} test exception",
            "created_at": now,
            "resolved_at": None,
            "resolved_by": None,
            "resolution_note": None,
        }

    client = TestClient(app)
    for status in statuses:
        response = client.get("/api/exceptions", params={"status": status})
        assert response.status_code == 200
        items = response.json()["data"]["items"]
        assert len(items) == 1
        assert items[0]["status"] == status

    open_response = client.get("/api/exceptions", params={"status": "OPEN"})
    assert [item["status"] for item in open_response.json()["data"]["items"]] == [
        "OPEN"
    ]


def test_exception_list_uses_supabase_repository_filters(monkeypatch) -> None:
    from app.repositories import exception_repository
    from app.services.exception_service import list_exceptions

    class Query:
        def __init__(self):
            self.calls = []

        def select(self, fields):
            self.calls.append(("select", fields))
            return self

        def eq(self, field, value):
            self.calls.append(("eq", field, value))
            return self

        def order(self, field, desc=False):
            self.calls.append(("order", field, desc))
            return self

        def limit(self, value):
            self.calls.append(("limit", value))
            return self

        def execute(self):
            return SimpleNamespace(data=[{"status": "OPEN"}])

    query = Query()
    monkeypatch.setattr(
        exception_repository,
        "get_settings",
        lambda: SimpleNamespace(supabase_configured=True),
    )
    monkeypatch.setattr(
        exception_repository,
        "get_supabase_client",
        lambda: SimpleNamespace(table=lambda table: query),
    )

    assert list_exceptions("OPEN", "CARDIOLOGY", 5) == (
        [{"status": "OPEN"}],
        None,
    )
    assert ("eq", "status", "OPEN") in query.calls
    assert ("eq", "assigned_role", "CARDIOLOGY") in query.calls
    assert ("limit", 6) in query.calls


def test_exception_pagination_uses_stable_created_at_and_id_order() -> None:
    from datetime import timedelta

    from app.core.database import get_database
    from app.repositories.exception_repository import list_exceptions

    database = get_database()
    base_time = datetime(2026, 10, 13, tzinfo=UTC)
    inserted = []
    for index in range(5):
        exception_id = str(uuid4())
        inserted.append(exception_id)
        database.exceptions[exception_id] = {
            "id": exception_id,
            "status": "OPEN" if index != 3 else "IN_PROGRESS",
            "assigned_role": "CARDIOLOGY",
            "created_at": base_time + timedelta(minutes=index),
        }

    first_page, cursor = list_exceptions("OPEN", "CARDIOLOGY", 2)
    assert [item["id"] for item in first_page] == [
        inserted[4],
        inserted[2],
    ]
    assert cursor is not None

    second_page, next_cursor = list_exceptions(
        "OPEN",
        "CARDIOLOGY",
        2,
        cursor,
    )
    assert [item["id"] for item in second_page] == [
        inserted[1],
        inserted[0],
    ]
    assert next_cursor is None


def test_exception_pagination_validates_cursor_and_filter_binding() -> None:
    from app.core.database import get_database
    from app.repositories.exception_repository import list_exceptions

    for _ in range(2):
        exception_id = str(uuid4())
        get_database().exceptions[exception_id] = {
            "id": exception_id,
            "status": "OPEN",
            "assigned_role": "CARDIOLOGY",
            "created_at": datetime.now(UTC),
        }
    _, cursor = list_exceptions("OPEN", "CARDIOLOGY", 1)
    assert cursor is not None

    invalid_payload = base64.urlsafe_b64encode(
        json.dumps(
            {
                "v": 1,
                "created_at": "not-a-date",
                "id": exception_id,
                "status": "OPEN",
                "assigned_role": "CARDIOLOGY",
            }
        ).encode()
    ).decode().rstrip("=")

    for bad_cursor, role in (
        ("not a cursor!", "CARDIOLOGY"),
        (invalid_payload, "CARDIOLOGY"),
        (cursor, "OTHER"),
    ):
        with pytest.raises(CareLoopError) as exc_info:
            list_exceptions("OPEN", role, 1, bad_cursor)
        assert exc_info.value.code == "INVALID_CURSOR"
        assert exc_info.value.status_code == 400


def test_exception_api_returns_and_consumes_next_cursor() -> None:
    from datetime import timedelta

    database = get_database()
    now = datetime.now(UTC)
    for index in range(3):
        exception_id = str(uuid4())
        database.exceptions[exception_id] = {
            "id": exception_id,
            "action_id": None,
            "handoff_id": None,
            "exception_type": "HANDOFF_OVERDUE",
            "status": "OPEN",
            "assigned_role": "CARDIOLOGY",
            "reason": f"Test exception {index}",
            "created_at": now + timedelta(minutes=index),
            "resolved_at": None,
            "resolved_by": None,
            "resolution_note": None,
        }

    client = TestClient(app)
    first = client.get(
        "/api/exceptions",
        params={"status": "OPEN", "assigned_role": "CARDIOLOGY", "limit": 2},
    )
    assert first.status_code == 200
    first_page = first.json()["data"]
    assert len(first_page["items"]) == 2
    assert first_page["next_cursor"]

    second = client.get(
        "/api/exceptions",
        params={
            "status": "OPEN",
            "assigned_role": "CARDIOLOGY",
            "limit": 2,
            "cursor": first_page["next_cursor"],
        },
    )
    assert second.status_code == 200
    second_page = second.json()["data"]
    assert len(second_page["items"]) == 1
    assert second_page["next_cursor"] is None

    invalid = client.get(
        "/api/exceptions",
        params={"cursor": "invalid cursor"},
    )
    assert invalid.status_code == 400
    assert invalid.json()["error"]["code"] == "INVALID_CURSOR"


def test_supabase_exception_pagination_uses_compound_cursor_filter(monkeypatch) -> None:
    from app.repositories import exception_repository
    from app.repositories.exception_repository import _encode_cursor, list_exceptions

    created_at = datetime(2026, 10, 13, tzinfo=UTC)
    boundary_id = str(uuid4())
    next_id = str(uuid4())

    class Query:
        def __init__(self):
            self.calls = []

        def select(self, fields):
            self.calls.append(("select", fields))
            return self

        def eq(self, field, value):
            self.calls.append(("eq", field, value))
            return self

        def or_(self, expression):
            self.calls.append(("or", expression))
            return self

        def order(self, field, desc=False):
            self.calls.append(("order", field, desc))
            return self

        def limit(self, value):
            self.calls.append(("limit", value))
            return self

        def execute(self):
            return SimpleNamespace(
                data=[
                    {
                        "id": next_id,
                        "created_at": "2026-10-12T00:00:00+00:00",
                        "status": "OPEN",
                        "assigned_role": "CARDIOLOGY",
                    },
                    {
                        "id": str(uuid4()),
                        "created_at": "2026-10-11T00:00:00+00:00",
                        "status": "OPEN",
                        "assigned_role": "CARDIOLOGY",
                    },
                ]
            )

    query = Query()
    monkeypatch.setattr(
        exception_repository,
        "get_settings",
        lambda: SimpleNamespace(supabase_configured=True),
    )
    monkeypatch.setattr(
        exception_repository,
        "get_supabase_client",
        lambda: SimpleNamespace(table=lambda table: query),
    )
    cursor = _encode_cursor(
        created_at,
        boundary_id,
        "OPEN",
        "CARDIOLOGY",
    )

    items, next_cursor = list_exceptions(
        "OPEN",
        "CARDIOLOGY",
        1,
        cursor,
    )

    assert len(items) == 1
    assert next_cursor is not None
    assert ("eq", "status", "OPEN") in query.calls
    assert ("eq", "assigned_role", "CARDIOLOGY") in query.calls
    assert any(
        call[0] == "or"
        and "created_at.lt.2026-10-13T00:00:00+00:00" in call[1]
        and f"id.lt.{boundary_id}" in call[1]
        for call in query.calls
    )
    assert ("order", "created_at", True) in query.calls
    assert ("order", "id", True) in query.calls
    assert ("limit", 2) in query.calls
