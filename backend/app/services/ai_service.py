from uuid import UUID


def classify_message(message: str, action_id: UUID | None) -> dict:
    normalized = message.lower()
    if any(word in normalized for word in ("could not", "can't", "cannot", "barrier", "transport")):
        intent = "BARRIER_REPORTED"
    elif any(word in normalized for word in ("reschedule", "another date", "change the date")):
        intent = "RESCHEDULE_REQUESTED"
    elif any(word in normalized for word in ("completed", "done", "finished")):
        intent = "COMPLETION_REPORTED"
    elif any(word in normalized for word in ("urgent", "severe", "emergency")):
        intent = "URGENT_CONCERN"
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
    return {"plan_id": str(plan_id), "proposed_actions": [], "requires_human_review": True}
