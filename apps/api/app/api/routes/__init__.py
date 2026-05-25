from fastapi import APIRouter

from app.api.routes.decisions import router as decisions_router
from app.api.routes.health import router as health_router

router = APIRouter()
router.include_router(health_router, prefix="/v1/health", tags=["health"])
router.include_router(decisions_router, prefix="/v1/decisions", tags=["decisions"])

