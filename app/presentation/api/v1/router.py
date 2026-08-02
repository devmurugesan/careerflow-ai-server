from fastapi import APIRouter
from app.presentation.api.v1.endpoints.health import router as health_router
from app.presentation.api.v1.endpoints.auth import router as auth_router
from app.presentation.api.v1.endpoints.gmail import router as gmail_router
from app.presentation.api.v1.endpoints.opportunities import router as opportunities_router
from app.presentation.api.v1.endpoints.dashboard import router as dashboard_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(gmail_router)
api_v1_router.include_router(opportunities_router)
api_v1_router.include_router(dashboard_router)
