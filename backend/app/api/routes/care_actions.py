from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException

from ...schemas.care_action import ActionEventRequest, CareAction, VerifyCompletionRequest
from ...schemas.common import success_response
from ...services.care_action_service import get_action, process_action_event, verify_completion


router = APIRouter()


@router.get("/care-actions/{action_id}")
def care_action(action_id: UUID) -> dict:
    try:
        return success_response(get_action(action_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/care-actions/{action_id}/start")
def start_action(action_id: UUID, payload: ActionEventRequest) -> dict:
    try:
        return success_response(process_action_event(action_id, "ACTION_STARTED", payload))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/care-actions/{action_id}/report-completion")
def report_completion(action_id: UUID, payload: ActionEventRequest) -> dict:
    try:
        return success_response(process_action_event(action_id, "COMPLETION_REPORTED", payload))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/care-actions/{action_id}/verify-completion")
def completion_verification(action_id: UUID, payload: VerifyCompletionRequest) -> dict:
    try:
        return success_response(verify_completion(action_id, payload))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
