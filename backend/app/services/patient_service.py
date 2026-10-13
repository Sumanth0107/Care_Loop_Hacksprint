
from datetime import UTC, datetime
from uuid import UUID, uuid4

from ..core.config import get_settings
from ..core.database import get_database
from ..repositories.patient_repository import (
    get_care_journey as get_persisted_care_journey,
)
from ..schemas.patient import CarePlanCreate
from .dependency_service import refresh_action_statuses


def get_care_plan(plan_id: UUID) -> dict:
    database = get_database()
    plan = database.care_plans.get(str(plan_id))

    if plan is None:
        raise KeyError(f"Care plan '{plan_id}' does not exist.")

    return plan


def get_journey(patient_id: UUID) -> dict:
    """Return a dashboard-ready journey from the configured data source."""

    if get_settings().supabase_configured:
        journey = get_persisted_care_journey(str(patient_id))

        if journey is None:
            raise KeyError(f"Patient '{patient_id}' does not exist.")

        plans = journey["care_plans"]

        if not plans:
            raise KeyError(
                f"No care plan exists for patient '{patient_id}'."
            )

        plan = max(plans, key=lambda item: item["version"])
        plan_id = str(plan["id"])

        actions = [
            action
            for action in journey["care_actions"]
            if str(action["care_plan_id"]) == plan_id
        ]

        actions_by_id = {
            str(action["id"]): action
            for action in actions
        }

        handoffs = [
            handoff
            for handoff in journey["handoffs"]
            if str(handoff["action_id"]) in actions_by_id
        ]

        handoffs_by_id = {
            str(handoff["id"]): handoff
            for handoff in handoffs
        }

        journey_actions = []

        for action in actions:
            action_dependencies = []

            for dependency in journey["dependencies"]:
                if str(dependency["action_id"]) != str(action["id"]):
                    continue

                requirement = dependency["requirement_type"]
                satisfied = False

                if requirement == "ACTION_VERIFIED":
                    prerequisite = actions_by_id.get(
                        str(dependency["depends_on_action_id"])
                    )
                    satisfied = (
                        prerequisite is not None
                        and prerequisite["status"] == "VERIFIED_COMPLETE"
                    )

                elif requirement == "HANDOFF_ACKNOWLEDGED":
                    required_handoff_id = dependency.get(
                        "required_handoff_id"
                    )
                    handoff = (
                        handoffs_by_id.get(str(required_handoff_id))
                        if required_handoff_id
                        else None
                    )
                    satisfied = (
                        handoff is not None
                        and handoff["status"] == "ACKNOWLEDGED"
                    )

                action_dependencies.append(
                    {
                        "requirement_type": requirement,
                        "satisfied": satisfied,
                    }
                )

            journey_actions.append(
                {
                    **action,
                    "dependencies": action_dependencies,
                }
            )

        active_exceptions = [
            exception
            for exception in journey["exceptions"]
            if exception["status"] in {"OPEN", "IN_PROGRESS"}
        ]

        return {
            "patient": journey["patient"],
            "care_plan": plan,
            "actions": journey_actions,
            "open_exception_count": len(active_exceptions),
        }

    # In-memory fallback for development and demo mode.
    database = get_database()
    patient = database.patients.get(str(patient_id))

    if patient is None:
        raise KeyError(f"Patient '{patient_id}' does not exist.")

    plans = [
        plan
        for plan in database.care_plans.values()
        if plan["patient_id"] == str(patient_id)
    ]

    if not plans:
        raise KeyError(
            f"No care plan exists for patient '{patient_id}'."
        )

    plan = max(plans, key=lambda item: item["version"])
    refresh_action_statuses()

    actions = [
        action
        for action in database.care_actions.values()
        if action["care_plan_id"] == plan["id"]
    ]

    action_ids = {str(action["id"]) for action in actions}

    handoffs = [
        handoff
        for handoff in database.handoffs.values()
        if str(handoff.get("action_id")) in action_ids
    ]

    journey_actions = []

    for action in actions:
        dependencies = [
            {
                "requirement_type": dependency["requirement_type"],
                "satisfied": _dependency_satisfied(dependency),
            }
            for dependency in database.dependencies
            if dependency["action_id"] == action["id"]
        ]

        journey_actions.append(
            {
                **action,
                "dependencies": dependencies,
            }
        )

    active_exceptions = [
        exception
        for exception in database.exceptions.values()
        if exception["status"] in {"OPEN", "IN_PROGRESS"}
        and (
            str(exception.get("action_id")) in action_ids
            or str(exception.get("handoff_id"))
            in {str(handoff["id"]) for handoff in handoffs}
        )
    ]

    return {
        "patient": patient,
        "care_plan": plan,
        "actions": journey_actions,
        "open_exception_count": len(active_exceptions),
    }


def _dependency_satisfied(dependency: dict) -> bool:
    """Evaluate a dependency using the in-memory database."""

    database = get_database()
    requirement = dependency["requirement_type"]

    if requirement == "ACTION_VERIFIED":
        prerequisite = database.care_actions.get(
            dependency["depends_on_action_id"]
        )
        return (
            prerequisite is not None
            and prerequisite["status"] == "VERIFIED_COMPLETE"
        )

    if requirement == "HANDOFF_ACKNOWLEDGED":
        handoff = database.handoffs.get(
            dependency.get("required_handoff_id")
        )
        return (
            handoff is not None
            and handoff["status"] == "ACKNOWLEDGED"
        )

    return False


def create_plan(payload: CarePlanCreate) -> dict:
    database = get_database()
    patient = database.patients.get(str(payload.patient_id))

    if patient is None:
        raise KeyError(
            f"Patient '{payload.patient_id}' does not exist."
        )

    now = datetime.now(UTC)
    plan_id = str(uuid4())

    versions = [
        plan["version"]
        for plan in database.care_plans.values()
        if plan["patient_id"] == str(payload.patient_id)
    ]

    plan = {
        "id": plan_id,
        "patient_id": str(payload.patient_id),
        "version": max(versions, default=0) + 1,
        "status": "DRAFT",
        "source_text": payload.source_text,
        "created_by": payload.created_by,
        "created_at": now,
        "updated_at": now,
    }

    database.care_plans[plan_id] = plan
    return plan


def parse_plan(plan_id: UUID) -> dict:
    plan = get_care_plan(plan_id)

    return {
        "plan_id": plan["id"],
        "proposed_actions": [],
        "requires_human_review": True,
    }


def approve_plan(plan_id: UUID) -> dict:
    plan = get_care_plan(plan_id)
    plan["status"] = "APPROVED"
    plan["updated_at"] = datetime.now(UTC)

    return plan
