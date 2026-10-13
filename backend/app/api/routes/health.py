from fastapi import APIRouter

from ...core.config import get_settings
from ...core.database import database_status
from ...schemas.common import success_response


router = APIRouter()


@router.get("/health")
def health() -> dict:
    settings = get_settings()
    return success_response(
        {
            "status": "ok",
            "service": settings.app_name,
            "environment": settings.environment,
            "database": database_status(settings),
        }
    )
