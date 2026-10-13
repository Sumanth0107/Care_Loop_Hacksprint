from fastapi import APIRouter, Query
from uuid import UUID

from ...schemas.common import success_response
from ...schemas.exception import ExceptionPatch
from ...services.exception_service import list_exceptions, update_exception


router = APIRouter()


@router.get("/exceptions")
def exceptions(
    status: str | None = Query(default=None),
    assigned_role: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
) -> dict:
    return success_response({"items": list_exceptions(status, assigned_role, limit), "next_cursor": None})


@router.patch("/exceptions/{exception_id}")
def patch_exception(exception_id: UUID, payload: ExceptionPatch) -> dict:
    return success_response(update_exception(exception_id, payload))
