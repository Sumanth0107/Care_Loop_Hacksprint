
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

ACTION_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"


@pytest.mark.parametrize(
    ("message", "expected_intent"),
    [
        (
            "I could not travel to the hospital because I had no transport.",
            "BARRIER_REPORTED",
        ),
        (
            "I need to reschedule my follow-up appointment.",
            "RESCHEDULE_REQUESTED",
        ),
        (
            "I have completed the prescribed follow-up task.",
            "COMPLETION_REPORTED",
        ),
        (
            "I have an urgent concern about my recovery.",
            "URGENT_CONCERN",
        ),
        (
            "I will think about it.",
            "UNCLEAR",
        ),
        (
            "I completed the task, but I could not travel to the hospital.",
            "BARRIER_REPORTED",
        ),
        (
            "I have an urgent concern and need to reschedule.",
            "URGENT_CONCERN",
        ),
    ],
)
def test_classify_message_returns_expected_intent(
    message: str, expected_intent: str
) -> None:
    response = client.post(
        "/api/ai/classify-message",
        json={"message": message, "action_id": ACTION_ID},
    )

    assert response.status_code == 200

    body = response.json()
    assert body["success"] is True
    assert body["data"]["intent"] == expected_intent
    assert body["data"]["action_id"] == ACTION_ID
    assert body["data"]["requires_human_review"] is True


def test_empty_message_is_handled_safely() -> None:
    response = client.post(
        "/api/ai/classify-message",
        json={"message": "", "action_id": ACTION_ID},
    )

    assert response.status_code == 200

    body = response.json()
    assert body["success"] is True
    assert body["data"]["intent"] == "UNCLEAR"
    assert body["data"]["requires_human_review"] is True

def test_negated_completion_is_not_reported_as_completed() -> None:
    response = client.post(
        "/api/ai/classify-message",
        json={
            "message": "I have not completed the task.",
            "action_id": ACTION_ID,
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["success"] is True
    assert body["data"]["intent"] == "UNCLEAR"
    assert body["data"]["requires_human_review"] is True
