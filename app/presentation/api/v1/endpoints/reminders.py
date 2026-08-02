from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.infrastructure.db.models.user import UserTable
from app.presentation.dependencies import get_current_user
from app.core.config import settings

reminders_router = APIRouter(prefix="/reminders", tags=["Reminders"])
analytics_router = APIRouter(prefix="/analytics", tags=["Analytics"])
settings_router = APIRouter(prefix="/settings", tags=["Settings"])


@reminders_router.get("")
async def get_reminders(current_user: UserTable = Depends(get_current_user)):
    """Gets active user reminders."""
    return {"user_id": str(current_user.id), "reminders": []}


@analytics_router.get("/funnel")
async def get_career_funnel(current_user: UserTable = Depends(get_current_user)):
    """Gets application conversion funnel analytics."""
    return {
        "user_id": str(current_user.id),
        "funnel": {
            "Registered": 12,
            "Assessment": 5,
            "Interview": 3,
            "Offer": 1,
            "Joined": 0
        }
    }


@settings_router.get("")
async def get_user_settings(current_user: UserTable = Depends(get_current_user)):
    """Gets current user configuration & AI settings."""
    return {
        "user_id": str(current_user.id),
        "primary_ai_provider": settings.PRIMARY_AI_PROVIDER,
        "fallback_ai_provider": settings.FALLBACK_AI_PROVIDER,
        "timezone": current_user.timezone
    }
