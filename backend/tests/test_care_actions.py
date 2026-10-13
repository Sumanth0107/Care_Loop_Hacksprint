from fastapi.testclient import TestClient

from app.main import app
from app.seed.demo_data import DEMO_ECG_ACTION_ID


def test_patient_report_waits_for_verification() -> None:
    client = TestClient(app)
    start_response = client.post(
        f"/api/care-actions/{DEMO_ECG_ACTION_ID}/start",
        json={
            "event_id": "99999999-9999-4999-8999-999999999999",
            "source": "DEPARTMENT",
            "actor_role": "DIAGNOSTICS",
            "occurred_at": "2026-10-13T08:10:00Z",
            "payload": {},
        },
    )
    assert start_response.status_code == 200
    response = client.post(
        f"/api/care-actions/{DEMO_ECG_ACTION_ID}/report-completion",
        json={
            "event_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
            "source": "PATIENT",
            "actor_role": "PATIENT",
            "occurred_at": "2026-10-13T08:20:00Z",
            "payload": {"message": "I completed the test."},
        },
    )
    assert response.status_code == 200
    assert response.json()["data"]["action"]["status"] == "AWAITING_VERIFICATION"
