
from uuid import uuid4

from fastapi import APIRouter

from ..core.database import database_status

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    return {
        "success": True,
        "data": {
            "status": "ok",
            "database": database_status(),
        },
        "meta": {
            "request_id": f"req-health-{uuid4().hex[:12]}"
        },
        "error": None,
    }
