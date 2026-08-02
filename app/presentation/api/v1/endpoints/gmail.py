from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.infrastructure.db.models import UserTable, GoogleCredentialTable
from app.presentation.dependencies import get_current_user

router = APIRouter(prefix="/gmail", tags=["Gmail Connection & Status"])


class GmailStatusResponseSchema(BaseModel):
    connected: bool
    email: Optional[str] = None
    scopes: Optional[str] = None
    expires_at: Optional[datetime] = None


@router.get("/status", response_model=GmailStatusResponseSchema)
async def get_gmail_connection_status(
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns safe connection status of user's Gmail OAuth account. Never returns raw tokens."""
    stmt = select(GoogleCredentialTable).where(GoogleCredentialTable.user_id == current_user.id)
    res = await db.execute(stmt)
    cred = res.scalar_one_or_none()

    if not cred or not cred.is_connected:
        return GmailStatusResponseSchema(connected=False)

    return GmailStatusResponseSchema(
        connected=True,
        email=current_user.email,
        scopes=cred.scopes,
        expires_at=cred.expires_at
    )


@router.post("/disconnect", status_code=status.HTTP_200_OK)
async def disconnect_gmail(
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Disconnects user's Gmail account by clearing OAuth credentials cleanly."""
    stmt = select(GoogleCredentialTable).where(GoogleCredentialTable.user_id == current_user.id)
    res = await db.execute(stmt)
    cred = res.scalar_one_or_none()

    if cred:
        cred.is_connected = False
        cred.encrypted_access_token = ""
        cred.encrypted_refresh_token = ""
        await db.commit()

    return {
        "message": "Gmail account disconnected successfully",
        "connected": False
    }
