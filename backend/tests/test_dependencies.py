from fastapi.testclient import TestClient

from app.main import app
from app.seed.demo_data import DEMO_PATIENT_ID


def test_journey_has_contract_shape() -> None:
    response = TestClient(app).get(f"/api/patients/{DEMO_PATIENT_ID}/care-journey")
    assert response.status_code == 200
    data = response.json()["data"]
    assert set(data) == {"patient", "care_plan", "actions", "open_exception_count"}
