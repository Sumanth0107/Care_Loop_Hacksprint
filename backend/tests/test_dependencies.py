from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.services import patient_service
from app.main import app
from app.seed.demo_data import DEMO_PATIENT_ID


def test_journey_has_contract_shape(monkeypatch) -> None:
    monkeypatch.setattr(
        patient_service,
        "get_settings",
        lambda: SimpleNamespace(supabase_configured=False),
    )
    response = TestClient(app).get(f"/api/patients/{DEMO_PATIENT_ID}/care-journey")
    assert response.status_code == 200

    data = response.json()["data"]
    assert set(data) == {
        "patient",
        "care_plan",
        "actions",
        "handoffs",
        "active_exceptions",
        "open_exception_count",
    }
    assert data["handoffs"] == []
    assert data["active_exceptions"] == []
