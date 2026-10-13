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
    cursor: str | None = Query(default=None),
) -> dict:
    items, next_cursor = list_exceptions(status, assigned_role, limit, cursor)
    return success_response({"items": items, "next_cursor": next_cursor})


@router.patch("/exceptions/{exception_id}")
def patch_exception(exception_id: UUID, payload: ExceptionPatch) -> dict:
    return success_response(update_exception(exception_id, payload))
