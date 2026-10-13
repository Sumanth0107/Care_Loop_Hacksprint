from datetime import UTC, datetime

from ..core.database import get_database


DEMO_PATIENT_ID = "11111111-1111-4111-8111-111111111111"
DEMO_PLAN_ID = "22222222-2222-4222-8222-222222222222"
DEMO_ECG_ACTION_ID = "33333333-3333-4333-8333-333333333333"
DEMO_REVIEW_ACTION_ID = "44444444-4444-4444-8444-444444444444"


def seed_demo_data() -> None:
    database = get_database()
    if database.patients:
        return
    now = datetime.now(UTC)
    database.patients[DEMO_PATIENT_ID] = {
        "id": DEMO_PATIENT_ID,
        "external_ref": "DEMO-001",
        "display_name": "Demo Patient",
        "created_at": now,
    }
    database.care_plans[DEMO_PLAN_ID] = {
        "id": DEMO_PLAN_ID,
        "patient_id": DEMO_PATIENT_ID,
        "version": 1,
        "status": "APPROVED",
        "source_text": "Complete an ECG, then perform a cardiology review.",
        "created_by": "demo-coordinator",
        "created_at": now,
        "updated_at": now,
    }
    database.care_actions[DEMO_ECG_ACTION_ID] = {
        "id": DEMO_ECG_ACTION_ID,
        "care_plan_id": DEMO_PLAN_ID,
        "title": "ECG",
        "description": "Complete the electrocardiogram.",
        "action_type": "DIAGNOSTIC",
        "status": "READY",
        "responsible_role": "DIAGNOSTICS",
        "due_at": None,
        "completion_reported_at": None,
        "verified_at": None,
        "verified_by": None,
        "created_at": now,
        "updated_at": now,
    }
    database.care_actions[DEMO_REVIEW_ACTION_ID] = {
        "id": DEMO_REVIEW_ACTION_ID,
        "care_plan_id": DEMO_PLAN_ID,
        "title": "Cardiology review",
        "description": "Review the ECG result.",
        "action_type": "REVIEW",
        "status": "PENDING",
        "responsible_role": "CARDIOLOGY",
        "due_at": None,
        "completion_reported_at": None,
        "verified_at": None,
        "verified_by": None,
        "created_at": now,
        "updated_at": now,
    }
    database.dependencies.append(
        {
            "id": "55555555-5555-4555-8555-555555555555",
            "action_id": DEMO_REVIEW_ACTION_ID,
            "depends_on_action_id": DEMO_ECG_ACTION_ID,
            "requirement_type": "ACTION_VERIFIED",
            "required_handoff_id": None,
        }
    )
