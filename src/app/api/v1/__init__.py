"""Version 1 of the OpenLabsX API routes."""

from fastapi import APIRouter

from .ranges import router as ranges_router
from .health import router as health_router
from .templates import router as templates_router

router = APIRouter(prefix="/v1")
router.include_router(health_router)
router.include_router(templates_router)
router.include_router(ranges_router)
