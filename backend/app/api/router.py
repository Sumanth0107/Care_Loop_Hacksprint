from fastapi import APIRouter

from .routes import ai, audit, care_actions, care_events, exceptions, handoffs, health, patients


api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(patients.router, tags=["patients"])
api_router.include_router(care_actions.router, tags=["care-actions"])
api_router.include_router(care_events.router, tags=["care-events"])
api_router.include_router(handoffs.router, tags=["handoffs"])
api_router.include_router(exceptions.router, tags=["exceptions"])
api_router.include_router(audit.router, tags=["audit"])
api_router.include_router(ai.router, tags=["ai"])
