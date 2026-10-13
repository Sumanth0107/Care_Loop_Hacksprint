from typing import Any, Generic, TypeVar
from uuid import uuid4

from pydantic import BaseModel, ConfigDict


T = TypeVar("T")


class Meta(BaseModel):
    request_id: str


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = {}


class ApiResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    success: bool
    data: T | None
    meta: Meta
    error: ErrorDetail | None


def success_response(data: Any, request_id: str | None = None) -> dict[str, Any]:
    return {
        "success": True,
        "data": data,
        "meta": {"request_id": request_id or f"req-{uuid4()}"},
        "error": None,
    }


def error_response(code: str, message: str, status_code: int, details: dict | None = None) -> tuple[dict, int]:
    return {
        "success": False,
        "data": None,
        "meta": {"request_id": f"req-{uuid4()}"},
        "error": {"code": code, "message": message, "details": details or {}},
    }, status_code
