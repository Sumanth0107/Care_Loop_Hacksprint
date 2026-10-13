from ..core.exceptions import CareLoopError


ALLOWED_TRANSITIONS = {
    "PENDING": {"READY", "CANCELLED"},
    "READY": {"IN_PROGRESS", "AWAITING_VERIFICATION", "BLOCKED", "CANCELLED"},
    "IN_PROGRESS": {"AWAITING_VERIFICATION", "BLOCKED", "CANCELLED"},
    "AWAITING_VERIFICATION": {"VERIFIED_COMPLETE"},
    "BLOCKED": {"READY", "CANCELLED"},
}


def transition(current: str, target: str) -> str:
    if target not in ALLOWED_TRANSITIONS.get(current, set()):
        raise CareLoopError(
            "INVALID_STATE_TRANSITION",
            f"Cannot transition care action from {current} to {target}.",
            status_code=409,
        )
    return target
