from uuid import UUID

from fastapi import APIRouter, Query

from ...schemas.common import success_response
from ...services.audit_service import list_audit


router = APIRouter()


@router.get("/audit")
def audit(entity_type: str | None = Query(default=None), entity_id: UUID | None = Query(default=None)) -> dict:
    return success_response({"items": list_audit(entity_type, entity_id)})
