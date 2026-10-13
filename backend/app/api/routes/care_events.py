from fastapi import APIRouter

from ...schemas.care_event import CareEventCreate
from ...schemas.common import success_response
from ...services.event_service import process_event


router = APIRouter()


@router.post("/care-events")
def care_event(payload: CareEventCreate) -> dict:
    return success_response(process_event(payload))
