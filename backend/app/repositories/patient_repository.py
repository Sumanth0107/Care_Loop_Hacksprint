
from typing import Any

from ..core.config import get_settings
from ..core.database import get_database, get_supabase_client


def get_patient(patient_id: str) -> dict[str, Any] | None:
    if not get_settings().supabase_configured:
        return get_database().patients.get(patient_id)

    client = get_supabase_client()
    response = (
        client.table("patients")
        .select("*")
        .eq("id", patient_id)
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None


def get_care_journey(patient_id: str) -> dict[str, Any] | None:
    """Retrieve a patient and related records from the configured data source."""

    if not get_settings().supabase_configured:
        db = get_database()
        patient = db.patients.get(patient_id)

        if patient is None:
            return None

        plans = [
            {**plan, "id": plan.get("id", key)}
            for key, plan in db.care_plans.items()
            if plan.get("patient_id") == patient_id
        ]
        plan_ids = {plan["id"] for plan in plans}

        actions = [
            {**action, "id": action.get("id", key)}
            for key, action in db.care_actions.items()
            if action.get("care_plan_id") in plan_ids
        ]
        action_ids = {action["id"] for action in actions}

        handoffs = [
            {**item, "id": item.get("id", key)}
            for key, item in db.handoffs.items()
            if item.get("action_id") in action_ids
        ]
        handoff_ids = {item["id"] for item in handoffs}

        exceptions = [
            {**item, "id": item.get("id", key)}
            for key, item in db.exceptions.items()
            if item.get("action_id") in action_ids
            or item.get("handoff_id") in handoff_ids
        ]

        dependencies = [
            item for item in db.dependencies
            if item.get("action_id") in action_ids
        ]

        return {
            "patient": patient,
            "care_plans": plans,
            "care_actions": actions,
            "handoffs": handoffs,
            "exceptions": exceptions,
            "dependencies": dependencies,
        }

    client = get_supabase_client()

    patient_response = (
        client.table("patients")
        .select("*")
        .eq("id", patient_id)
        .limit(1)
        .execute()
    )
    if not patient_response.data:
        return None

    patient = patient_response.data[0]

    plans_response = (
        client.table("care_plans")
        .select("*")
        .eq("patient_id", patient_id)
        .execute()
    )
    plans = plans_response.data or []
    plan_ids = [plan["id"] for plan in plans]

    actions = []
    if plan_ids:
        actions_response = (
            client.table("care_actions")
            .select("*")
            .in_("care_plan_id", plan_ids)
            .execute()
        )
        actions = actions_response.data or []

    action_ids = [action["id"] for action in actions]

    dependencies = []
    handoffs = []
    exceptions_by_id = {}

    if action_ids:
        dependency_response = (
            client.table("action_dependencies")
            .select("*")
            .in_("action_id", action_ids)
            .execute()
        )
        dependencies = dependency_response.data or []

        handoff_response = (
            client.table("handoffs")
            .select("*")
            .in_("action_id", action_ids)
            .execute()
        )
        handoffs = handoff_response.data or []

        exception_response = (
            client.table("exceptions")
            .select("*")
            .in_("action_id", action_ids)
            .execute()
        )
        for item in exception_response.data or []:
            exceptions_by_id[item["id"]] = item

    handoff_ids = [handoff["id"] for handoff in handoffs]
    if handoff_ids:
        exception_response = (
            client.table("exceptions")
            .select("*")
            .in_("handoff_id", handoff_ids)
            .execute()
        )
        for item in exception_response.data or []:
            exceptions_by_id[item["id"]] = item

    return {
        "patient": patient,
        "care_plans": plans,
        "care_actions": actions,
        "handoffs": handoffs,
        "exceptions": list(exceptions_by_id.values()),
        "dependencies": dependencies,
    }
