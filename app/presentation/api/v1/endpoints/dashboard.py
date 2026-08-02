from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.infrastructure.db.models import UserTable
from app.services.dashboard_service import DashboardService
from app.presentation.dependencies import get_current_user
from app.domain.dashboard.schemas import (
    DashboardSummarySchema,
    UpcomingOpportunitySchema,
    RecentActivitySchema,
    CoursesDashboardSchema,
    CompaniesDashboardSchema,
    HackathonsDashboardSchema,
    CertificateItemSchema,
    PaginatedOpportunitySearchResultSchema
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard Intelligence"])


@router.get("/summary", response_model=DashboardSummarySchema)
async def get_dashboard_summary(
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves real-time aggregated opportunity dashboard status counts."""
    service = DashboardService(db)
    return await service.get_dashboard_summary(current_user.id)


@router.get("/upcoming", response_model=List[UpcomingOpportunitySchema])
async def get_upcoming_opportunities(
    limit: int = Query(10, ge=1, le=50),
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves upcoming opportunities sorted by nearest deadline."""
    service = DashboardService(db)
    return await service.get_upcoming_opportunities(current_user.id, limit=limit)


@router.get("/recent", response_model=List[RecentActivitySchema])
async def get_recent_activity(
    limit: int = Query(10, ge=1, le=50),
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves recent updates and status transition activity."""
    service = DashboardService(db)
    return await service.get_recent_activity(current_user.id, limit=limit)


@router.get("/courses", response_model=CoursesDashboardSchema)
async def get_courses_dashboard(
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves active courses, completed courses, progress %, and certificates ready."""
    service = DashboardService(db)
    return await service.get_courses_dashboard(current_user.id)


@router.get("/companies", response_model=CompaniesDashboardSchema)
async def get_companies_dashboard(
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves company job applications grouped by Applied, Assessment, Interview, Offer, Rejected, Joined."""
    service = DashboardService(db)
    return await service.get_companies_dashboard(current_user.id)


@router.get("/hackathons", response_model=HackathonsDashboardSchema)
async def get_hackathons_dashboard(
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves hackathons grouped by Registered, Round 1, Round 2, Finalist, Winner, Completed."""
    service = DashboardService(db)
    return await service.get_hackathons_dashboard(current_user.id)


@router.get("/certificates", response_model=List[CertificateItemSchema])
async def get_certificates(
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves every completed certification and available certificate."""
    service = DashboardService(db)
    return await service.get_certificates(current_user.id)


@router.get("/search", response_model=PaginatedOpportunitySearchResultSchema)
async def search_and_filter_opportunities(
    q: Optional[str] = Query(None, description="Search keyword across title, org, category, status"),
    category: Optional[str] = Query(None, description="Filter by opportunity category"),
    status: Optional[str] = Query(None, description="Filter by current status"),
    organization: Optional[str] = Query(None, description="Filter by organization or platform"),
    priority: Optional[str] = Query(None, description="Filter by priority (LOW, MEDIUM, HIGH, URGENT)"),
    date_from: Optional[datetime] = Query(None, description="Filter by created date start"),
    date_to: Optional[datetime] = Query(None, description="Filter by created date end"),
    sort_by: str = Query("updated_at", description="Sort by field: deadline, last_updated, created_date, priority, title"),
    order: str = Query("desc", description="Sort order: asc or desc"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Search, filter, sort, and paginate opportunities."""
    service = DashboardService(db)
    return await service.search_and_filter_opportunities(
        user_id=current_user.id,
        q=q,
        category=category,
        status=status,
        organization=organization,
        priority=priority,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort_by,
        order=order,
        page=page,
        page_size=page_size
    )
