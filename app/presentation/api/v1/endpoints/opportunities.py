import uuid
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.infrastructure.db.models import UserTable
from app.infrastructure.db.repositories.opportunity_repo import OpportunityRepository
from app.services.opportunity_service import OpportunityService
from app.presentation.dependencies import get_current_user

router = APIRouter(prefix="/opportunities", tags=["Opportunity Management"])


class OpportunityResponseSchema(BaseModel):
    id: str
    category: str
    title: str
    organization_or_platform: str
    current_status: str
    priority: str
    deadline: Optional[datetime]
    event_date: Optional[datetime]
    action_required: Optional[str]
    summary: Optional[str]
    confidence_score: float
    updated_at: datetime


class OpportunityTimelineItemSchema(BaseModel):
    id: str
    timestamp: str
    event_type: str
    from_status: str
    to_status: str
    summary: Optional[str]
    email_subject: str
    source_email_id: Optional[str]
    action_required: Optional[str]


class OpportunityUpdateSchema(BaseModel):
    current_status: Optional[str] = None
    priority: Optional[str] = None
    action_required: Optional[str] = None
    is_archived: Optional[bool] = None


@router.get("", response_model=List[OpportunityResponseSchema])
async def list_opportunities(
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 50,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lists user opportunities with optional filtering by category, status, and search query."""
    repo = OpportunityRepository(db)
    items = await repo.get_user_opportunities(
        current_user.id, category=category, status=status, search=search, skip=skip, limit=limit
    )
    return [
        OpportunityResponseSchema(
            id=str(item.id),
            category=item.category,
            title=item.title,
            organization_or_platform=item.organization_or_platform,
            current_status=item.current_status,
            priority=item.priority,
            deadline=item.deadline,
            event_date=item.event_date,
            action_required=item.action_required,
            summary=item.summary,
            confidence_score=item.confidence_score,
            updated_at=item.updated_at
        ) for item in items
    ]


@router.get("/timeline/{id}", response_model=List[OpportunityTimelineItemSchema])
@router.get("/{id}/timeline", response_model=List[OpportunityTimelineItemSchema])
async def get_opportunity_timeline(
    id: str,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Fetches chronological event timeline for a specific opportunity without exposing email bodies."""
    service = OpportunityService(db)
    try:
        opp_id = uuid.UUID(id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Opportunity UUID format")

    timeline = await service.get_opportunity_timeline(current_user.id, opp_id)
    if timeline is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    return [OpportunityTimelineItemSchema(**item) for item in timeline]


@router.get("/{id}", response_model=OpportunityResponseSchema)
async def get_opportunity(
    id: str,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Gets details of a specific opportunity."""
    repo = OpportunityRepository(db)
    try:
        opp_id = uuid.UUID(id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Opportunity UUID format")

    item = await repo.get_by_id(opp_id)
    if not item or item.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    return OpportunityResponseSchema(
        id=str(item.id),
        category=item.category,
        title=item.title,
        organization_or_platform=item.organization_or_platform,
        current_status=item.current_status,
        priority=item.priority,
        deadline=item.deadline,
        event_date=item.event_date,
        action_required=item.action_required,
        summary=item.summary,
        confidence_score=item.confidence_score,
        updated_at=item.updated_at
    )


@router.patch("/{id}", response_model=OpportunityResponseSchema)
async def update_opportunity(
    id: str,
    data: OpportunityUpdateSchema,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Manually updates opportunity status, priority, or action notes."""
    repo = OpportunityRepository(db)
    try:
        opp_id = uuid.UUID(id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Opportunity UUID format")

    item = await repo.get_by_id(opp_id)
    if not item or item.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    if data.current_status:
        item.current_status = data.current_status
    if data.priority:
        item.priority = data.priority
    if data.action_required is not None:
        item.action_required = data.action_required
    if data.is_archived is not None:
        item.is_archived = data.is_archived

    await repo.save(item)
    return OpportunityResponseSchema(
        id=str(item.id),
        category=item.category,
        title=item.title,
        organization_or_platform=item.organization_or_platform,
        current_status=item.current_status,
        priority=item.priority,
        deadline=item.deadline,
        event_date=item.event_date,
        action_required=item.action_required,
        summary=item.summary,
        confidence_score=item.confidence_score,
        updated_at=item.updated_at
    )
