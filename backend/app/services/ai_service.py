import re
from uuid import UUID


def classify_message(message: str, action_id: UUID | None) -> dict:
    normalized = message.lower()
    words = set(re.findall(r"\b[\w']+\b", normalized))

    # Give urgent concerns priority over routine requests.
    if any(word in words for word in ("urgent", "severe", "emergency")):
        intent = "URGENT_CONCERN"

    # A negated completion must not be treated as confirmed completion.
    elif (
        any(word in words for word in ("completed", "done", "finished"))
        and not re.search(
            r"\b(?:not|never|haven't|hasn't|hadn't|didn't|did not)\b"
            r".{0,30}\b(?:completed|done|finished)\b",
            normalized,
        )
        and not re.search(
            r"\b(?:completed|done|finished)\b"
            r".{0,20}\b(?:not|yet|never)\b",
            normalized,
        )
    ):
        # Preserve the existing precedence for reported barriers.
        if any(
            phrase in normalized
            for phrase in ("could not", "can't", "cannot", "barrier", "transport")
        ):
            intent = "BARRIER_REPORTED"
        else:
            intent = "COMPLETION_REPORTED"

    elif any(
        phrase in normalized
        for phrase in ("could not", "can't", "cannot", "barrier", "transport")
    ):
        intent = "BARRIER_REPORTED"

    elif any(
        phrase in normalized
        for phrase in ("reschedule", "another date", "change the date")
    ):
        intent = "RESCHEDULE_REQUESTED"

    elif "?" in message:
        intent = "QUESTION"

    else:
        intent = "UNCLEAR"

    return {
        "intent": intent,
        "action_id": str(action_id) if action_id else None,
        "confidence": 0.75 if intent != "UNCLEAR" else 0.35,
        "requires_human_review": True,
    }


def extract_care_plan(source_text: str, plan_id: UUID) -> dict:
    return {
        "plan_id": str(plan_id),
        "proposed_actions": [],
        "requires_human_review": True,
    }