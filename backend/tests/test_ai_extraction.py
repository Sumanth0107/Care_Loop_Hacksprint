
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

PLAN_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"


def test_extract_care_plan_requires_human_review() -> None:
    response = client.post(
        "/api/ai/extract-care-plan",
        json={
            "source_text": (
                "Patient reports difficulty attending follow-up "
                "because transportation is unavailable."
            ),
            "plan_id": PLAN_ID,
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["success"] is True

    data = body["data"]
    assert data["plan_id"] == PLAN_ID
    assert isinstance(data["proposed_actions"], list)
    assert data["requires_human_review"] is True


def test_extract_care_plan_handles_empty_proposed_actions() -> None:
    response = client.post(
        "/api/ai/extract-care-plan",
        json={
            "source_text": "",
            "plan_id": PLAN_ID,
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["success"] is True

    data = body["data"]
    assert data["proposed_actions"] == []
    assert data["requires_human_review"] is True
