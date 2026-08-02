import math
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.repositories.opportunity_repo import OpportunityRepository
from app.domain.dashboard.schemas import (
    DashboardSummarySchema,
    CategorySummary,
    CompanySummary,
    HackathonSummary,
    SingleCountSummary,
    OverallSummary,
    UpcomingOpportunitySchema,
    RecentActivitySchema,
    CourseOpportunityItemSchema,
    CoursesDashboardSchema,
    CompanyOpportunityItemSchema,
    CompaniesDashboardSchema,
    HackathonOpportunityItemSchema,
    HackathonsDashboardSchema,
    CertificateItemSchema,
    OpportunitySearchItemSchema,
    PaginatedOpportunitySearchResultSchema
)


class DashboardService:
    """Service handling aggregated business logic for Dashboard backend APIs."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = OpportunityRepository(session)

    async def get_dashboard_summary(self, user_id: uuid.UUID) -> DashboardSummarySchema:
        raw_summary = await self.repo.get_dashboard_summary_counts(user_id)
        breakdown = raw_summary.get("category_breakdown", {})

        courses_total = 0
        courses_active = 0
        courses_completed = 0
        courses_certs = 0

        companies_apps = 0
        companies_assessments = 0
        companies_interviews = 0
        companies_offers = 0

        hackathons_registered = 0
        hackathons_active = 0
        hackathons_completed = 0

        internships_active = 0
        scholarships_active = 0
        coding_contests_active = 0

        total_opps = 0
        overall_active = 0
        overall_completed = 0

        for cat, status_dict in breakdown.items():
            cat_lower = cat.lower() if cat else ""

            for status, count in status_dict.items():
                st_lower = status.lower() if status else ""
                total_opps += count

                # Overall Completed check
                is_completed = any(kw in st_lower for kw in ["completed", "joined", "winner", "awarded", "certificate available", "certificate received"])
                if is_completed:
                    overall_completed += count
                else:
                    overall_active += count

                # Category 1: Courses & Certifications
                if "course" in cat_lower or "certification" in cat_lower or "certificate" in cat_lower:
                    courses_total += count
                    if "completed" in st_lower or "certificate" in st_lower:
                        courses_completed += count
                        if "certificate" in st_lower:
                            courses_certs += count
                    else:
                        courses_active += count

                # Category 2: Companies & Internships
                elif any(kw in cat_lower for kw in ["company", "recruitment", "internship"]):
                    if "internship" in cat_lower:
                        if not is_completed and "rejected" not in st_lower:
                            internships_active += count

                    if "applied" in st_lower or "registered" in st_lower or "application" in st_lower:
                        companies_apps += count
                    elif "assessment" in st_lower or "test" in st_lower:
                        companies_assessments += count
                    elif "interview" in st_lower:
                        companies_interviews += count
                    elif "offer" in st_lower or "selected" in st_lower or "joined" in st_lower:
                        companies_offers += count

                # Category 3: Hackathons
                elif "hackathon" in cat_lower:
                    if "registered" in st_lower:
                        hackathons_registered += count
                    if is_completed:
                        hackathons_completed += count
                    else:
                        hackathons_active += count

                # Category 4: Scholarships
                elif "scholarship" in cat_lower:
                    if not is_completed:
                        scholarships_active += count

                # Category 5: Coding Contests
                elif "contest" in cat_lower:
                    if not is_completed:
                        coding_contests_active += count

        return DashboardSummarySchema(
            courses=CategorySummary(
                total=courses_total,
                active=courses_active,
                completed=courses_completed,
                certificates_ready=courses_certs
            ),
            companies=CompanySummary(
                applications=companies_apps,
                assessments=companies_assessments,
                interviews=companies_interviews,
                offers=companies_offers
            ),
            hackathons=HackathonSummary(
                registered=hackathons_registered,
                active=hackathons_active,
                completed=hackathons_completed
            ),
            internships=SingleCountSummary(active=internships_active),
            scholarships=SingleCountSummary(active=scholarships_active),
            coding_contests=SingleCountSummary(active=coding_contests_active),
            overall=OverallSummary(
                total_opportunities=total_opps,
                active=overall_active,
                completed=overall_completed
            )
        )

    async def get_upcoming_opportunities(self, user_id: uuid.UUID, limit: int = 10) -> List[UpcomingOpportunitySchema]:
        items = await self.repo.get_upcoming_by_deadline(user_id, limit=limit)
        now = datetime.now(timezone.utc)

        res = []
        for item in items:
            days = 0
            if item.deadline:
                delta = item.deadline - now
                days = max(0, delta.days)

            res.append(UpcomingOpportunitySchema(
                id=str(item.id),
                title=item.title,
                category=item.category,
                organization=item.organization_or_platform,
                current_state=item.current_status,
                deadline=item.deadline,
                days_remaining=days,
                priority=item.priority
            ))
        return res

    async def get_recent_activity(self, user_id: uuid.UUID, limit: int = 10) -> List[RecentActivitySchema]:
        items = await self.repo.get_recent_updated(user_id, limit=limit)

        res = []
        for item in items:
            prev_state = "Registered"
            if item.status_history and len(item.status_history) > 0:
                prev_state = item.status_history[-1].from_status

            res.append(RecentActivitySchema(
                id=str(item.id),
                title=item.title,
                category=item.category,
                organization=item.organization_or_platform,
                new_state=item.current_status,
                previous_state=prev_state,
                updated_at=item.updated_at,
                summary=item.summary
            ))
        return res

    async def get_courses_dashboard(self, user_id: uuid.UUID) -> CoursesDashboardSchema:
        items = await self.repo.get_opportunities_by_categories(user_id, ["Course", "Certification", "Certificate"])

        active_courses = []
        completed_courses = []
        certificates_ready = []
        total_progress = 0.0
        timeline_events = []

        for item in items:
            st_lower = item.current_status.lower()
            progress = 0.0
            if item.course_detail and item.course_detail.completion_percentage:
                progress = float(item.course_detail.completion_percentage)

            is_cert_ready = "certificate" in st_lower
            is_completed = "completed" in st_lower or is_cert_ready
            if is_completed and progress == 0.0:
                progress = 100.0

            total_progress += progress

            course_schema = CourseOpportunityItemSchema(
                id=str(item.id),
                title=item.title,
                organization=item.organization_or_platform,
                current_state=item.current_status,
                progress_percentage=progress,
                certificate_ready=is_cert_ready,
                updated_at=item.updated_at
            )

            if is_cert_ready:
                certificates_ready.append(course_schema)
            if is_completed:
                completed_courses.append(course_schema)
            else:
                active_courses.append(course_schema)

            if item.status_history:
                for h in item.status_history:
                    timeline_events.append({
                        "course_title": item.title,
                        "state": h.to_status,
                        "date": h.changed_at.isoformat() if h.changed_at else item.updated_at.isoformat(),
                        "summary": h.reason_summary or item.summary
                    })

        avg_progress = round(total_progress / len(items), 1) if items else 0.0

        return CoursesDashboardSchema(
            active_courses=active_courses,
            completed_courses=completed_courses,
            certificates_ready=certificates_ready,
            average_progress_percentage=avg_progress,
            timeline_summary=timeline_events
        )

    async def get_companies_dashboard(self, user_id: uuid.UUID) -> CompaniesDashboardSchema:
        items = await self.repo.get_opportunities_by_categories(user_id, ["Company Recruitment", "Company", "Internship", "Assessment"])

        applied = []
        assessment = []
        interview = []
        offer = []
        rejected = []
        joined = []

        for item in items:
            st_lower = item.current_status.lower()
            schema = CompanyOpportunityItemSchema(
                id=str(item.id),
                title=item.title,
                organization=item.organization_or_platform,
                current_state=item.current_status,
                priority=item.priority,
                deadline=item.deadline,
                event_date=item.event_date,
                action_required=item.action_required,
                updated_at=item.updated_at
            )

            if "rejected" in st_lower or "withdrawn" in st_lower:
                rejected.append(schema)
            elif "joined" in st_lower or "hired" in st_lower:
                joined.append(schema)
            elif "offer" in st_lower or "selected" in st_lower:
                offer.append(schema)
            elif "interview" in st_lower:
                interview.append(schema)
            elif "assessment" in st_lower or "test" in st_lower:
                assessment.append(schema)
            else:
                applied.append(schema)

        return CompaniesDashboardSchema(
            applied=applied,
            assessment=assessment,
            interview=interview,
            offer=offer,
            rejected=rejected,
            joined=joined
        )

    async def get_hackathons_dashboard(self, user_id: uuid.UUID) -> HackathonsDashboardSchema:
        items = await self.repo.get_opportunities_by_categories(user_id, ["Hackathon", "Coding Contest"])

        registered = []
        round_1 = []
        round_2 = []
        finalist = []
        winner = []
        completed = []

        for item in items:
            st_lower = item.current_status.lower()
            schema = HackathonOpportunityItemSchema(
                id=str(item.id),
                title=item.title,
                organization=item.organization_or_platform,
                current_state=item.current_status,
                deadline=item.deadline,
                event_date=item.event_date,
                updated_at=item.updated_at
            )

            if "winner" in st_lower or "won" in st_lower:
                winner.append(schema)
            elif "finalist" in st_lower or "final" in st_lower:
                finalist.append(schema)
            elif "round 2" in st_lower:
                round_2.append(schema)
            elif "round 1" in st_lower:
                round_1.append(schema)
            elif "completed" in st_lower:
                completed.append(schema)
            else:
                registered.append(schema)

        return HackathonsDashboardSchema(
            registered=registered,
            round_1=round_1,
            round_2=round_2,
            finalist=finalist,
            winner=winner,
            completed=completed
        )

    async def get_certificates(self, user_id: uuid.UUID) -> List[CertificateItemSchema]:
        items = await self.repo.get_opportunities_by_categories(user_id, ["Course", "Certification", "Certificate"])

        certs = []
        for item in items:
            st_lower = item.current_status.lower()
            if "completed" in st_lower or "certificate" in st_lower or "awarded" in st_lower:
                cert_url = None
                if item.course_detail and item.course_detail.certificate_url:
                    cert_url = item.course_detail.certificate_url

                certs.append(CertificateItemSchema(
                    id=str(item.id),
                    title=item.title,
                    organization=item.organization_or_platform,
                    completion_date=item.updated_at,
                    certificate_status="Available" if "certificate" in st_lower else "Completed",
                    certificate_url=cert_url
                ))
        return certs

    async def search_and_filter_opportunities(
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
    ) -> PaginatedOpportunitySearchResultSchema:
        items, total = await self.repo.search_filter_paginate_opportunities(
            user_id=user_id,
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

        total_pages = math.ceil(total / page_size) if total > 0 else 1

        search_items = [
            OpportunitySearchItemSchema(
                id=str(item.id),
                category=item.category,
                title=item.title,
                organization=item.organization_or_platform,
                current_state=item.current_status,
                priority=item.priority,
                deadline=item.deadline,
                event_date=item.event_date,
                summary=item.summary,
                created_at=item.created_at,
                updated_at=item.updated_at
            ) for item in items
        ]

        return PaginatedOpportunitySearchResultSchema(
            items=search_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
