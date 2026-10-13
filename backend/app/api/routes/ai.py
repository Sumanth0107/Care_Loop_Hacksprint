from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from ...schemas.common import success_response
from ...services.ai_service import classify_message, extract_care_plan


router = APIRouter()


class ClassifyMessageRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str
    action_id: UUID | None = None


class ExtractCarePlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_text: str
    plan_id: UUID


@router.post("/ai/classify-message")
def classify(payload: ClassifyMessageRequest) -> dict:
    return success_response(classify_message(payload.message, payload.action_id))


@router.post("/ai/extract-care-plan")
def extract(payload: ExtractCarePlanRequest) -> dict:
    return success_response(extract_care_plan(payload.source_text, payload.plan_id))
