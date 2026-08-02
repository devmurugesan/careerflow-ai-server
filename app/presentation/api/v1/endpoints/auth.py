from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AuthenticationException
from app.infrastructure.google.oauth_service import GoogleOAuthService
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication & Google OAuth"])


class TokenResponseSchema(BaseModel):
    message: str
    user: Dict[str, Any]
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@router.get("/google", status_code=status.HTTP_200_OK)
async def initiate_google_oauth(state: Optional[str] = Query(None)):
    """Initiates Google OAuth 2.0 flow by returning authorization URL."""
    try:
        auth_url = GoogleOAuthService.get_authorization_url(state=state)
        return {
            "authorization_url": auth_url,
            "state": state
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/google/callback", response_model=TokenResponseSchema)
async def google_oauth_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Callback endpoint for Google OAuth authorization code exchange."""
    if error:
        if error == "access_denied":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User denied Google OAuth consent"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google OAuth authorization error: {error}"
        )

    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing authorization code parameter"
        )

    service = AuthService(db)
    result = await service.authenticate_google_user(code)
    return TokenResponseSchema(**result)
