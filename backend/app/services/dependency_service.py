from ..core.database import get_database


def dependencies_satisfied(action_id: str) -> bool:
    database = get_database()
    dependencies = [item for item in database.dependencies if item["action_id"] == action_id]
    return all(
        item["requirement_type"] == "ACTION_VERIFIED"
        and database.care_actions[item["depends_on_action_id"]]["status"] == "VERIFIED_COMPLETE"
        or item["requirement_type"] == "HANDOFF_ACKNOWLEDGED"
        and database.handoffs[item["required_handoff_id"]]["status"] == "ACKNOWLEDGED"
        for item in dependencies
    )


def refresh_action_statuses() -> None:
    database = get_database()
    for action in database.care_actions.values():
        if action["status"] == "PENDING" and dependencies_satisfied(action["id"]):
            action["status"] = "READY"
