from uuid import UUID

from fastapi import APIRouter, HTTPException

from ...schemas.common import success_response
from ...schemas.handoff import HandoffCreate, HandoffEventRequest
from ...services.handoff_service import acknowledge_handoff, create_handoff, send_handoff


router = APIRouter()


@router.post("/handoffs", status_code=201)
def handoff(payload: HandoffCreate) -> dict:
    try:
        return success_response(create_handoff(payload))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/handoffs/{handoff_id}/send")
def send(handoff_id: UUID, payload: HandoffEventRequest) -> dict:
    try:
        return success_response(send_handoff(handoff_id, payload))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/handoffs/{handoff_id}/acknowledge")
def acknowledge(handoff_id: UUID, payload: HandoffEventRequest) -> dict:
    try:
        return success_response(acknowledge_handoff(handoff_id, payload))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
