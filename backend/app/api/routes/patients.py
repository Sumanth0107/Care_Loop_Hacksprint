from uuid import UUID

from fastapi import APIRouter, HTTPException

from ...schemas.common import success_response
from ...schemas.patient import CarePlanCreate
from ...schemas.journey import CareJourneyEnvelope
from ...services.patient_service import get_care_plan, get_journey


router = APIRouter()


@router.get("/patients/{patient_id}/care-journey")
def care_journey(patient_id: UUID) -> dict:
    try:
        return success_response(get_journey(patient_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/care-plans/{plan_id}")
def care_plan(plan_id: UUID) -> dict:
    try:
        return success_response(get_care_plan(plan_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/care-plans", status_code=201)
def create_care_plan(payload: CarePlanCreate) -> dict:
    from ...services.patient_service import create_plan

    plan = create_plan(CarePlanCreate.model_validate(payload))
    return success_response(plan)


@router.post("/care-plans/{plan_id}/parse")
def parse_care_plan(plan_id: UUID) -> dict:
    from ...services.patient_service import parse_plan

    try:
        return success_response(parse_plan(plan_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/care-plans/{plan_id}/approve")
def approve_care_plan(plan_id: UUID) -> dict:
    from ...services.patient_service import approve_plan

    try:
        return success_response(approve_plan(plan_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
