class CareLoopError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class ResourceNotFoundError(CareLoopError):
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            "RESOURCE_NOT_FOUND",
            f"{resource} '{resource_id}' does not exist.",
            status_code=404,
        )
