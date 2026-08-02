import uuid
from typing import List, Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy import select, func, update, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.infrastructure.db.models import OpportunityTable, OpportunityEmailTable, OpportunityStatusHistoryTable, EmailTable


class OpportunityRepository:
    """Repository handling database operations for Opportunity Aggregate Root."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, opportunity_id: uuid.UUID) -> Optional[OpportunityTable]:
        stmt = (
            select(OpportunityTable)
            .where(OpportunityTable.id == opportunity_id)
            .options(
                selectinload(OpportunityTable.email_links).selectinload(OpportunityEmailTable.email),
                selectinload(OpportunityTable.status_history)
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_candidate_opportunities(self, user_id: uuid.UUID) -> List[OpportunityTable]:
        """Fetches active user opportunities for weighted matching engine."""
        stmt = (
            select(OpportunityTable)
            .where(
                and_(
                    OpportunityTable.user_id == user_id,
                    OpportunityTable.is_archived == False
                )
            )
            .options(
                selectinload(OpportunityTable.email_links).selectinload(OpportunityEmailTable.email)
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_by_title_and_org(
        self, user_id: uuid.UUID, title: str, org: str, category: str
    ) -> Optional[OpportunityTable]:
        stmt = select(OpportunityTable).where(
            and_(
                OpportunityTable.user_id == user_id,
                OpportunityTable.category == category,
                func.lower(OpportunityTable.title) == title.lower(),
                func.lower(OpportunityTable.organization_or_platform) == org.lower()
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_opportunities(
        self,
        user_id: uuid.UUID,
        category: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[OpportunityTable]:
        query = select(OpportunityTable).where(
            and_(OpportunityTable.user_id == user_id, OpportunityTable.is_archived == False)
        )
        if category:
            query = query.where(OpportunityTable.category == category)
        if status:
            query = query.where(OpportunityTable.current_status == status)
        if search:
            search_term = f"%{search.lower()}%"
            query = query.where(
                (func.lower(OpportunityTable.title).like(search_term)) |
                (func.lower(OpportunityTable.organization_or_platform).like(search_term))
            )

        query = query.order_by(OpportunityTable.updated_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_dashboard_summary_counts(self, user_id: uuid.UUID) -> dict:
        """High-performance SQL query returning category & status counts for dashboard."""
        stmt = (
            select(
                OpportunityTable.category,
                OpportunityTable.current_status,
                func.count(OpportunityTable.id)
            )
            .where(and_(OpportunityTable.user_id == user_id, OpportunityTable.is_archived == False))
            .group_by(OpportunityTable.category, OpportunityTable.current_status)
        )
        result = await self.session.execute(stmt)

        counts = {}
        total_active = 0
        for category, status, count in result.all():
            total_active += count
            if category not in counts:
                counts[category] = {}
            counts[category][status] = count

        return {
            "total_active_opportunities": total_active,
            "category_breakdown": counts
        }

    async def get_upcoming_by_deadline(self, user_id: uuid.UUID, limit: int = 10) -> List[OpportunityTable]:
        """Fetches upcoming opportunities sorted by nearest deadline (deadline >= now)."""
        now = datetime.now(timezone.utc)
        stmt = (
            select(OpportunityTable)
            .where(
                and_(
                    OpportunityTable.user_id == user_id,
                    OpportunityTable.is_archived == False,
                    OpportunityTable.deadline != None,
                    OpportunityTable.deadline >= now
                )
            )
            .order_by(OpportunityTable.deadline.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_recent_updated(self, user_id: uuid.UUID, limit: int = 10) -> List[OpportunityTable]:
        """Fetches recently updated opportunities with status history eager loaded."""
        stmt = (
            select(OpportunityTable)
            .where(
                and_(
                    OpportunityTable.user_id == user_id,
                    OpportunityTable.is_archived == False
                )
            )
            .options(selectinload(OpportunityTable.status_history))
            .order_by(OpportunityTable.updated_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_opportunities_by_categories(self, user_id: uuid.UUID, categories: List[str]) -> List[OpportunityTable]:
        """Fetches active opportunities matching given category strings."""
        stmt = (
            select(OpportunityTable)
            .where(
                and_(
                    OpportunityTable.user_id == user_id,
                    OpportunityTable.is_archived == False,
                    OpportunityTable.category.in_(categories)
                )
            )
            .options(
                selectinload(OpportunityTable.course_detail),
                selectinload(OpportunityTable.status_history)
            )
            .order_by(OpportunityTable.updated_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def search_filter_paginate_opportunities(
        self,
        user_id: uuid.UUID,
        q: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        organization: Optional[str] = None,
        priority: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        sort_by: str = "updated_at",
        order: str = "desc",
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[OpportunityTable], int]:
        """Flexible search, filter, sort, and pagination query."""
        query = select(OpportunityTable).where(
            and_(OpportunityTable.user_id == user_id, OpportunityTable.is_archived == False)
        )

        # Keyword search (title, org, category, status)
        if q:
            term = f"%{q.strip().lower()}%"
            query = query.where(
                or_(
                    func.lower(OpportunityTable.title).like(term),
                    func.lower(OpportunityTable.organization_or_platform).like(term),
                    func.lower(OpportunityTable.category).like(term),
                    func.lower(OpportunityTable.current_status).like(term)
                )
            )

        if category:
            query = query.where(func.lower(OpportunityTable.category) == category.strip().lower())
        if status:
            query = query.where(func.lower(OpportunityTable.current_status) == status.strip().lower())
        if organization:
            query = query.where(func.lower(OpportunityTable.organization_or_platform).like(f"%{organization.strip().lower()}%"))
        if priority:
            query = query.where(func.upper(OpportunityTable.priority) == priority.strip().upper())
        if date_from:
            query = query.where(OpportunityTable.created_at >= date_from)
        if date_to:
            query = query.where(OpportunityTable.created_at <= date_to)

        # Total count query
        count_stmt = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        # Sorting
        sort_column = getattr(OpportunityTable, sort_by, OpportunityTable.updated_at)
        if sort_by == "deadline":
            sort_column = OpportunityTable.deadline
        elif sort_by == "created_date":
            sort_column = OpportunityTable.created_at
        elif sort_by == "last_updated":
            sort_column = OpportunityTable.updated_at
        elif sort_by == "priority":
            sort_column = OpportunityTable.priority
        elif sort_by == "title":
            sort_column = OpportunityTable.title

        direction = desc if order.lower() == "desc" else asc
        query = query.order_by(direction(sort_column))

        # Pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.session.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def save(self, opportunity: OpportunityTable) -> OpportunityTable:
        self.session.add(opportunity)
        await self.session.flush()
        return opportunity
