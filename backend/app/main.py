
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.routes import ai, audit, care_actions, care_events, exceptions, handoffs, health, patients
from .core.config import get_settings
from .core.exceptions import CareLoopError
from .schemas.common import error_response
from .seed.demo_data import seed_demo_data

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")

seed_demo_data()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(CareLoopError)
async def care_loop_error_handler(_: Request, exc: CareLoopError) -> JSONResponse:
    body, status_code = error_response(
        exc.code, exc.message, exc.status_code, exc.details
    )
    return JSONResponse(status_code=status_code, content=body)


for route_module, tags in (
    (health, ["health"]),
    (patients, ["patients"]),
    (care_actions, ["care-actions"]),
    (care_events, ["care-events"]),
    (handoffs, ["handoffs"]),
    (exceptions, ["exceptions"]),
    (audit, ["audit"]),
    (ai, ["ai"]),
):
    app.include_router(
        route_module.router,
        prefix=settings.api_prefix,
        tags=tags,
    )
