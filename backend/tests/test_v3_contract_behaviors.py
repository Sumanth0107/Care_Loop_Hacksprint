from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_database
from app.core.exceptions import CareLoopError
from app.main import app
from app.schemas.care_event import CareEventCreate
from app.services.audit_service import list_audit
from app.services.dependency_service import refresh_action_statuses
from app.services.event_service import process_event
from app.services.exception_service import update_exception
from app.services.handoff_service import acknowledge_handoff, reject_handoff, send_handoff


def _make_action(action_id: str, *, title: str = "ECG", status: str = "PENDING", care_plan_id: str = "plan-1") -> str:
    database = get_database()
    now = datetime.now(UTC)
    database.care_actions[action_id] = {
        "id": action_id,
        "care_plan_id": care_plan_id,
        "title": title,
        "description": "Test action",
        "action_type": "DIAGNOSTIC",
        "status": status,
        "responsible_role": "DIAGNOSTICS",
        "due_at": None,
        "completion_reported_at": None,
        "verified_at": None,
        "verified_by": None,
        "created_at": now,
        "updated_at": now,
    }
    return action_id


def _make_handoff(action_id: str, handoff_id: str | None = None) -> str:
    database = get_database()
    handoff_id = handoff_id or str(uuid4())
    database.handoffs[handoff_id] = {
        "id": handoff_id,
        "action_id": action_id,
        "recipient_role": "CARDIOLOGY",
        "recipient_id": "demo-cardiology",
        "status": "PENDING",
        "sent_at": None,
        "acknowledged_at": None,
        "acknowledged_by": None,
        "deadline_at": datetime.now(UTC),
        "rejection_reason": None,
        "created_at": datetime.now(UTC),
    }
    return handoff_id


def _make_exception(action_id: str, handoff_id: str | None = None) -> str:
    database = get_database()
    exception_id = str(uuid4())
    database.exceptions[exception_id] = {
        "id": exception_id,
        "action_id": action_id,
        "handoff_id": handoff_id,
        "exception_type": "HANDOFF_OVERDUE",
        "status": "OPEN",
        "assigned_role": "CARDIOLOGY",
        "reason": "Required acknowledgment has not arrived.",
        "resolution_note": None,
        "created_at": datetime.now(UTC),
        "resolved_at": None,
        "resolved_by": None,
    }
    return exception_id


def _care_event(**kwargs):
    event = {
        "event_id": kwargs.get("event_id") or uuid4(),
        "event_type": kwargs["event_type"],
        "action_id": kwargs.get("action_id"),
        "handoff_id": kwargs.get("handoff_id"),
        "source": kwargs["source"],
        "actor": kwargs["actor"],
        "occurred_at": kwargs.get("occurred_at") or datetime.now(UTC),
        "payload": kwargs.get("payload", {}),
    }
    return CareEventCreate.model_validate(event)


def _request_payload(**kwargs):
    return SimpleNamespace(
        event_id=kwargs.get("event_id") or uuid4(),
        actor_id=kwargs.get("actor_id"),
        actor_role=kwargs.get("actor_role"),
        actor=kwargs.get("actor"),
        occurred_at=kwargs.get("occurred_at") or datetime.now(UTC),
        payload=kwargs.get("payload", {}),
    )


def test_all_six_canonical_events_dispatch_to_correct_service_logic() -> None:
    database = get_database()
    action_id = str(uuid4())
    handoff_id = str(uuid4())
    _make_action(action_id, status="READY")
    _make_handoff(action_id, handoff_id)

    process_event(_care_event(event_type="ACTION_STARTED", action_id=action_id, source="DEPARTMENT", actor={"id": "diag-team", "role": "DIAGNOSTICS"}))
    assert database.care_actions[action_id]["status"] == "IN_PROGRESS"

    process_event(_care_event(event_type="COMPLETION_REPORTED", action_id=action_id, source="PATIENT", actor={"id": "demo-patient", "role": "PATIENT"}, payload={"message": "I completed the test."}))
    assert database.care_actions[action_id]["status"] == "AWAITING_VERIFICATION"

    process_event(_care_event(event_type="COMPLETION_VERIFIED", action_id=action_id, source="CARE_COORDINATOR", actor={"id": "care-coordinator", "role": "CARE_COORDINATOR"}, payload={"evidence_id": str(uuid4()), "verification_note": "approved"}))
    assert database.care_actions[action_id]["status"] == "VERIFIED_COMPLETE"

    database.handoffs[handoff_id]["status"] = "PENDING"
    process_event(_care_event(event_type="HANDOFF_SENT", handoff_id=handoff_id, source="CARE_COORDINATOR", actor={"id": "care-coordinator", "role": "CARE_COORDINATOR"}))
    assert database.handoffs[handoff_id]["status"] == "SENT"

    process_event(_care_event(event_type="HANDOFF_ACKNOWLEDGED", handoff_id=handoff_id, source="DEPARTMENT_SIMULATOR", actor={"id": "demo-cardiology", "role": "CARDIOLOGY"}, payload={"receipt_reference": "demo-ack"}))
    assert database.handoffs[handoff_id]["status"] == "ACKNOWLEDGED"

    rejected_handoff_id = _make_handoff(action_id)
    database.handoffs[rejected_handoff_id]["status"] = "SENT"
    process_event(_care_event(event_type="HANDOFF_REJECTED", handoff_id=rejected_handoff_id, source="DEPARTMENT_SIMULATOR", actor={"id": "demo-cardiology", "role": "CARDIOLOGY"}, payload={"reason": "recipient rejected"}))
    assert database.handoffs[rejected_handoff_id]["status"] == "REJECTED"


def test_nested_and_legacy_flat_actor_payloads_are_both_supported() -> None:
    client = TestClient(app)
    action_id = _make_action(str(uuid4()), status="READY")

    nested_response = client.post(
        f"/api/care-actions/{action_id}/start",
        json={
            "event_id": str(uuid4()),
            "source": "DEPARTMENT",
            "actor": {"id": "diag-team", "role": "DIAGNOSTICS"},
            "occurred_at": "2026-10-13T08:10:00Z",
            "payload": {},
        },
    )
    assert nested_response.status_code == 200
    assert nested_response.json()["data"]["action"]["status"] == "IN_PROGRESS"

    legacy_response = client.post(
        f"/api/care-actions/{action_id}/report-completion",
        json={
            "event_id": str(uuid4()),
            "source": "PATIENT",
            "actor_id": "demo-patient",
            "actor_role": "PATIENT",
            "occurred_at": "2026-10-13T08:20:00Z",
            "payload": {"message": "I completed the test."},
        },
    )
    assert legacy_response.status_code == 200
    assert legacy_response.json()["data"]["action"]["status"] == "AWAITING_VERIFICATION"


def test_completion_reporting_cannot_bypass_verification() -> None:
    action_id = _make_action(str(uuid4()), status="READY")
    client = TestClient(app)

    response = client.post(
        f"/api/care-actions/{action_id}/report-completion",
        json={
            "event_id": str(uuid4()),
            "source": "PATIENT",
            "actor": {"id": "demo-patient", "role": "PATIENT"},
            "occurred_at": "2026-10-13T08:20:00Z",
            "payload": {"message": "I completed the test."},
        },
    )
    assert response.status_code == 200
    assert response.json()["data"]["action"]["status"] == "AWAITING_VERIFICATION"
    assert response.json()["data"]["action"]["status"] != "VERIFIED_COMPLETE"


def test_care_journey_returns_persisted_handoffs_and_active_exceptions(
    monkeypatch,
) -> None:
    from types import SimpleNamespace

    from app.services import patient_service
    from app.seed.demo_data import DEMO_ECG_ACTION_ID, DEMO_PATIENT_ID

    monkeypatch.setattr(
        patient_service,
        "get_settings",
        lambda: SimpleNamespace(supabase_configured=False),
    )
    database = get_database()
    handoff_id = str(uuid4())
    now = datetime.now(UTC)
    database.handoffs[handoff_id] = {
        "id": handoff_id,
        "action_id": DEMO_ECG_ACTION_ID,
        "recipient_role": "CARDIOLOGY",
        "recipient_id": None,
        "status": "PENDING",
        "sent_at": None,
        "acknowledged_at": None,
        "acknowledged_by": None,
        "deadline_at": now,
        "rejection_reason": None,
        "created_at": now,
    }
    exception_ids = {}
    for status in ("OPEN", "IN_PROGRESS", "RESOLVED", "DISMISSED"):
        exception_id = str(uuid4())
        exception_ids[status] = exception_id
        database.exceptions[exception_id] = {
            "id": exception_id,
            "action_id": DEMO_ECG_ACTION_ID,
            "handoff_id": handoff_id,
            "exception_type": "HANDOFF_OVERDUE",
            "status": status,
            "assigned_role": "CARDIOLOGY",
            "reason": f"{status} test exception.",
            "resolution_note": None,
            "created_at": now,
            "resolved_at": None,
            "resolved_by": None,
        }
    response = TestClient(app).get(
        f"/api/patients/{DEMO_PATIENT_ID}/care-journey"
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert [handoff["id"] for handoff in data["handoffs"]] == [handoff_id]
    assert {
        exception["status"] for exception in data["active_exceptions"]
    } == {"OPEN", "IN_PROGRESS"}
    assert {exception["id"] for exception in data["active_exceptions"]} == {
        exception_ids["OPEN"],
        exception_ids["IN_PROGRESS"],
    }
    assert data["open_exception_count"] == 2


def test_handoff_ack_and_reject_follow_distinct_valid_transitions() -> None:
    action_id = _make_action(str(uuid4()), status="READY")
    handoff_id = _make_handoff(action_id)

    with pytest.raises(CareLoopError, match="INVALID_STATE_TRANSITION"):
        acknowledge_handoff(handoff_id, _request_payload(actor_id="demo-cardiology", actor_role="CARDIOLOGY"))

    send_handoff(handoff_id, _request_payload(actor_id="demo-coordinator", actor_role="CARE_COORDINATOR"))
    reject_handoff(handoff_id, _request_payload(actor_id="demo-cardiology", actor_role="CARDIOLOGY", payload={"reason": "not needed"}))
    assert get_database().handoffs[str(handoff_id)]["status"] == "REJECTED"

    second_handoff_id = _make_handoff(action_id)
    with pytest.raises(CareLoopError, match="INVALID_STATE_TRANSITION"):
        reject_handoff(second_handoff_id, _request_payload(actor_id="demo-cardiology", actor_role="CARDIOLOGY", payload={"reason": "bad"}))


def test_required_state_changes_persist_in_database_and_dependencies_block_until_satisfied() -> None:
    database = get_database()
    plan_id = str(uuid4())
    prerequisite_id = str(uuid4())
    dependent_id = str(uuid4())
    _make_action(prerequisite_id, title="ECG", care_plan_id=plan_id, status="READY")
    _make_action(dependent_id, title="Cardiology review", care_plan_id=plan_id, status="PENDING")
    database.dependencies.append(
        {
            "id": str(uuid4()),
            "action_id": dependent_id,
            "depends_on_action_id": prerequisite_id,
            "requirement_type": "ACTION_VERIFIED",
            "required_handoff_id": None,
        }
    )

    refresh_action_statuses()
    assert database.care_actions[dependent_id]["status"] == "PENDING"

    database.care_actions[prerequisite_id]["status"] = "VERIFIED_COMPLETE"
    refresh_action_statuses()
    assert database.care_actions[dependent_id]["status"] == "READY"


def test_exception_resolution_and_audit_history_are_consistent() -> None:
    action_id = _make_action(str(uuid4()), status="READY")
    handoff_id = _make_handoff(action_id)
    exception_id = _make_exception(action_id, handoff_id)

    update_exception(
        exception_id,
        SimpleNamespace(status="RESOLVED", assigned_role="CARDIOLOGY", resolution_note="Acknowledged", actor_id="care-coordinator"),
    )

    exception = get_database().exceptions[str(exception_id)]
    assert exception["status"] == "RESOLVED"
    assert exception["resolved_by"] == "care-coordinator"
    audit_entries = list_audit("exception", exception_id)
    assert audit_entries
    assert any(entry["operation"] == "STATUS_CHANGED" for entry in audit_entries)


def test_replayed_events_do_not_duplicate_side_effects() -> None:
    database = get_database()
    action_id = _make_action(str(uuid4()), status="READY")
    event = _care_event(event_type="ACTION_STARTED", action_id=action_id, source="DEPARTMENT", actor={"id": "diag-team", "role": "DIAGNOSTICS"})

    first = process_event(event)
    second = process_event(event)

    assert first == second
    assert len(database.care_events) == 1
    assert database.care_actions[action_id]["status"] == "IN_PROGRESS"


def test_database_failures_do_not_return_false_success(monkeypatch) -> None:
    import app.services.event_service as event_service

    class FailingDict(dict):
        def __setitem__(self, key, value):
            raise RuntimeError("db failure")

    bad_database = SimpleNamespace(care_events=FailingDict())
    monkeypatch.setattr(event_service, "get_database", lambda: bad_database)

    with pytest.raises(CareLoopError, match="INTERNAL_ERROR"):
        process_event(
            _care_event(
                event_type="ACTION_STARTED",
                action_id=str(uuid4()),
                source="DEPARTMENT",
                actor={"id": "diag-team", "role": "DIAGNOSTICS"},
            )
        )


def test_v3_routes_remain_compatible_with_nested_actor_payloads() -> None:
    client = TestClient(app)
    action_id = _make_action(str(uuid4()), status="READY")

    nested_event = client.post(
        "/api/care-events",
        json={
            "event_id": str(uuid4()),
            "event_type": "COMPLETION_REPORTED",
            "action_id": action_id,
            "source": "PATIENT",
            "actor": {"id": "demo-patient", "role": "PATIENT"},
            "occurred_at": "2026-10-13T08:20:00Z",
            "payload": {"message": "I completed the test."},
        },
    )
    assert nested_event.status_code == 200
    assert nested_event.json()["data"]["action"]["status"] == "AWAITING_VERIFICATION"
