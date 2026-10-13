from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.database import get_database
from app.main import app


def test_audit_list_uses_supabase_filters_without_writing(monkeypatch) -> None:
    from app.repositories import audit_repository

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

        def execute(self):
            return SimpleNamespace(
                data=[
                    {
                        "entity_type": "care_action",
                        "entity_id": "33333333-3333-4333-8333-333333333333",
                        "operation": "STATUS_CHANGED",
                    }
                ]
            )

    query = Query()
    monkeypatch.setattr(
        audit_repository,
        "get_settings",
        lambda: SimpleNamespace(supabase_configured=True),
    )
    monkeypatch.setattr(
        audit_repository,
        "get_supabase_client",
        lambda: SimpleNamespace(table=lambda table: query),
    )

    entity_id = uuid4()
    response = TestClient(app).get(
        "/api/audit",
        params={"entity_type": "care_action", "entity_id": str(entity_id)},
    )

    assert response.status_code == 200
    assert response.json()["data"]["items"][0]["operation"] == "STATUS_CHANGED"
    assert ("eq", "entity_type", "care_action") in query.calls
    assert ("eq", "entity_id", str(entity_id)) in query.calls
    assert ("order", "created_at", True) in query.calls


def test_record_audit_keeps_memory_transitions_out_of_supabase_repository(
    monkeypatch,
) -> None:
    from app.repositories import audit_repository
    from app.services import audit_service

    def fail_on_write(entry):
        raise AssertionError("memory transition attempted a Supabase audit write")

    monkeypatch.setattr(
        audit_repository,
        "insert_audit_entry",
        fail_on_write,
    )
    database_entries = get_database().audit_log
    audit_service.record_audit(
        "care_action",
        "33333333-3333-4333-8333-333333333333",
        "STATUS_CHANGED",
        "coordinator",
        "CARE_COORDINATOR",
        {"status": "PENDING"},
        {"status": "IN_PROGRESS"},
        str(uuid4()),
    )

    assert len(database_entries) == 1
    assert database_entries[0]["operation"] == "STATUS_CHANGED"
    assert database_entries[0]["entity_type"] == "care_action"


def test_audit_insert_resolves_event_foreign_key_and_encodes_states(monkeypatch) -> None:
    from app.repositories import audit_repository

    care_event_id = str(uuid4())
    submitted_payload = {}

    class Query:
        def __init__(self, table):
            self.table_name = table
            self.filters = []

        def select(self, fields):
            return self

        def eq(self, field, value):
            self.filters.append((field, value))
            return self

        def limit(self, value):
            return self

        def insert(self, payload):
            submitted_payload.update(payload)
            return self

        def execute(self):
            if self.table_name == "care_events":
                return SimpleNamespace(data=[{"id": care_event_id}])
            return SimpleNamespace(data=[submitted_payload])

    monkeypatch.setattr(
        audit_repository,
        "get_settings",
        lambda: SimpleNamespace(supabase_configured=True),
    )
    monkeypatch.setattr(
        audit_repository,
        "get_supabase_client",
        lambda: SimpleNamespace(table=Query),
    )

    occurred_at = datetime(2026, 10, 13, tzinfo=UTC)
    result = audit_repository.insert_audit_entry(
        {
            "event_id": str(uuid4()),
            "entity_type": "handoff",
            "entity_id": str(uuid4()),
            "operation": "HANDOFF_SENT",
            "actor_role": "CARE_COORDINATOR",
            "before_state": {"occurred_at": occurred_at},
            "after_state": {"status": "SENT"},
        }
    )

    assert submitted_payload["event_id"] == care_event_id
    assert submitted_payload["before_state"]["occurred_at"] == occurred_at.isoformat()
    assert result["operation"] == "HANDOFF_SENT"


def test_audit_insert_rejects_missing_event_reference_before_writing(
    monkeypatch,
) -> None:
    import pytest

    from app.repositories import audit_repository

    inserted_tables = []

    class Query:
        def __init__(self, table):
            self.table_name = table

        def select(self, fields):
            return self

        def eq(self, field, value):
            return self

        def limit(self, value):
            return self

        def insert(self, payload):
            inserted_tables.append(self.table_name)
            return self

        def execute(self):
            return SimpleNamespace(data=[])

    monkeypatch.setattr(
        audit_repository,
        "get_settings",
        lambda: SimpleNamespace(supabase_configured=True),
    )
    monkeypatch.setattr(
        audit_repository,
        "get_supabase_client",
        lambda: SimpleNamespace(table=Query),
    )

    with pytest.raises(ValueError, match="does not exist"):
        audit_repository.insert_audit_entry(
            {
                "event_id": str(uuid4()),
                "entity_type": "handoff",
                "entity_id": str(uuid4()),
                "operation": "HANDOFF_SENT",
                "actor_role": "CARE_COORDINATOR",
            }
        )

    assert inserted_tables == []
