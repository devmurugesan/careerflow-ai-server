import uuid
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

from app.services.dashboard_service import DashboardService
from app.infrastructure.db.models import OpportunityTable, UserTable, CourseTable
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


@pytest.mark.asyncio
async def test_dashboard_summary_exact_structure():
    user_id = uuid.uuid4()
    mock_session = AsyncMock()

    service = DashboardService(mock_session)
    service.repo.get_dashboard_summary_counts = AsyncMock(return_value={
        "total_active_opportunities": 5,
        "category_breakdown": {
            "Course": {"Registered": 1, "Completed": 1},
            "Company Recruitment": {"Application Submitted": 1, "Interview Scheduled": 1},
            "Hackathon": {"Registered": 1}
        }
    })

    summary = await service.get_dashboard_summary(user_id)
    assert isinstance(summary, DashboardSummarySchema)

    # Check exact contract fields
    assert hasattr(summary, "courses")
    assert hasattr(summary, "companies")
    assert hasattr(summary, "hackathons")
    assert hasattr(summary, "internships")
    assert hasattr(summary, "scholarships")
    assert hasattr(summary, "coding_contests")
    assert hasattr(summary, "overall")

    assert summary.courses.total == 2
    assert summary.courses.active == 1
    assert summary.courses.completed == 1

    assert summary.companies.applications == 1
    assert summary.companies.interviews == 1

    assert summary.hackathons.registered == 1
    assert summary.overall.total_opportunities == 5


@pytest.mark.asyncio
async def test_upcoming_deadlines_sorting_and_days_remaining():
    user_id = uuid.uuid4()
    mock_session = AsyncMock()

    now = datetime.now(timezone.utc)
    deadline_near = now + timedelta(days=2)
    deadline_far = now + timedelta(days=10)

    opp1 = OpportunityTable(
        id=uuid.uuid4(),
        user_id=user_id,
        category="Company Recruitment",
        title="Software Engineer",
        organization_or_platform="Google",
        current_status="Assessment Pending",
        priority="HIGH",
        deadline=deadline_near,
        is_archived=False
    )
    opp2 = OpportunityTable(
        id=uuid.uuid4(),
        user_id=user_id,
        category="Hackathon",
        title="AI Hackathon 2026",
        organization_or_platform="Devpost",
        current_status="Registered",
        priority="MEDIUM",
        deadline=deadline_far,
        is_archived=False
    )

    service = DashboardService(mock_session)
    service.repo.get_upcoming_by_deadline = AsyncMock(return_value=[opp1, opp2])

    upcoming = await service.get_upcoming_opportunities(user_id, limit=10)
    assert len(upcoming) == 2
    assert upcoming[0].title == "Software Engineer"
    assert upcoming[0].days_remaining in [1, 2]
    assert upcoming[1].days_remaining in [9, 10]


@pytest.mark.asyncio
async def test_recent_activity():
    user_id = uuid.uuid4()
    mock_session = AsyncMock()

    now = datetime.now(timezone.utc)
    opp = OpportunityTable(
        id=uuid.uuid4(),
        user_id=user_id,
        category="Course",
        title="Python Data Analysis",
        organization_or_platform="Coursera",
        current_status="Completed",
        summary="Completed Python course",
        updated_at=now,
        is_archived=False,
        status_history=[]
    )

    service = DashboardService(mock_session)
    service.repo.get_recent_updated = AsyncMock(return_value=[opp])

    recent = await service.get_recent_activity(user_id, limit=10)
    assert len(recent) == 1
    assert recent[0].new_state == "Completed"
    assert recent[0].organization == "Coursera"


@pytest.mark.asyncio
async def test_courses_dashboard_grouping():
    user_id = uuid.uuid4()
    mock_session = AsyncMock()

    c1 = OpportunityTable(
        id=uuid.uuid4(),
        user_id=user_id,
        category="Course",
        title="Machine Learning",
        organization_or_platform="Coursera",
        current_status="In Progress",
        updated_at=datetime.now(timezone.utc),
        is_archived=False,
        course_detail=CourseTable(platform_name="Coursera", course_name="Machine Learning", completion_percentage=60),
        status_history=[]
    )
    c2 = OpportunityTable(
        id=uuid.uuid4(),
        user_id=user_id,
        category="Course",
        title="Deep Learning",
        organization_or_platform="Coursera",
        current_status="Certificate Available",
        updated_at=datetime.now(timezone.utc),
        is_archived=False,
        course_detail=CourseTable(platform_name="Coursera", course_name="Deep Learning", completion_percentage=100),
        status_history=[]
    )

    service = DashboardService(mock_session)
    service.repo.get_opportunities_by_categories = AsyncMock(return_value=[c1, c2])

    res = await service.get_courses_dashboard(user_id)
    assert isinstance(res, CoursesDashboardSchema)
    assert len(res.active_courses) == 1
    assert len(res.completed_courses) == 1
    assert len(res.certificates_ready) == 1
    assert res.average_progress_percentage == 80.0


@pytest.mark.asyncio
async def test_companies_dashboard_grouping():
    user_id = uuid.uuid4()
    mock_session = AsyncMock()

    app1 = OpportunityTable(
        id=uuid.uuid4(), user_id=user_id, category="Company Recruitment",
        title="Backend Dev", organization_or_platform="Google",
        current_status="Application Submitted", priority="HIGH", updated_at=datetime.now(timezone.utc), is_archived=False
    )
    app2 = OpportunityTable(
        id=uuid.uuid4(), user_id=user_id, category="Company Recruitment",
        title="Frontend Dev", organization_or_platform="Meta",
        current_status="Interview Scheduled", priority="HIGH", updated_at=datetime.now(timezone.utc), is_archived=False
    )
    app3 = OpportunityTable(
        id=uuid.uuid4(), user_id=user_id, category="Company Recruitment",
        title="SDE", organization_or_platform="Amazon",
        current_status="Rejected", priority="LOW", updated_at=datetime.now(timezone.utc), is_archived=False
    )

    service = DashboardService(mock_session)
    service.repo.get_opportunities_by_categories = AsyncMock(return_value=[app1, app2, app3])

    res = await service.get_companies_dashboard(user_id)
    assert isinstance(res, CompaniesDashboardSchema)
    assert len(res.applied) == 1
    assert len(res.interview) == 1
    assert len(res.rejected) == 1


@pytest.mark.asyncio
async def test_hackathons_dashboard_grouping():
    user_id = uuid.uuid4()
    mock_session = AsyncMock()

    h1 = OpportunityTable(
        id=uuid.uuid4(), user_id=user_id, category="Hackathon",
        title="Global Hack 2026", organization_or_platform="Devpost",
        current_status="Registered", updated_at=datetime.now(timezone.utc), is_archived=False
    )
    h2 = OpportunityTable(
        id=uuid.uuid4(), user_id=user_id, category="Hackathon",
        title="Web3 Hackathon", organization_or_platform="ETHGlobal",
        current_status="Winner", updated_at=datetime.now(timezone.utc), is_archived=False
    )

    service = DashboardService(mock_session)
    service.repo.get_opportunities_by_categories = AsyncMock(return_value=[h1, h2])

    res = await service.get_hackathons_dashboard(user_id)
    assert isinstance(res, HackathonsDashboardSchema)
    assert len(res.registered) == 1
    assert len(res.winner) == 1


@pytest.mark.asyncio
async def test_certificates_listing():
    user_id = uuid.uuid4()
    mock_session = AsyncMock()

    c1 = OpportunityTable(
        id=uuid.uuid4(), user_id=user_id, category="Course",
        title="Full Stack Specialization", organization_or_platform="Coursera",
        current_status="Certificate Available", updated_at=datetime.now(timezone.utc), is_archived=False,
        course_detail=CourseTable(platform_name="Coursera", course_name="Full Stack", certificate_url="https://coursera.org/verify/123")
    )

    service = DashboardService(mock_session)
    service.repo.get_opportunities_by_categories = AsyncMock(return_value=[c1])

    certs = await service.get_certificates(user_id)
    assert len(certs) == 1
    assert certs[0].title == "Full Stack Specialization"
    assert certs[0].certificate_url == "https://coursera.org/verify/123"


@pytest.mark.asyncio
async def test_dashboard_search_filter_pagination():
    user_id = uuid.uuid4()
    mock_session = AsyncMock()

    item1 = OpportunityTable(
        id=uuid.uuid4(), user_id=user_id, category="Course",
        title="Python Data Science", organization_or_platform="Coursera",
        current_status="In Progress", priority="MEDIUM",
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc), is_archived=False
    )

    service = DashboardService(mock_session)
    service.repo.search_filter_paginate_opportunities = AsyncMock(return_value=([item1], 1))

    res = await service.search_and_filter_opportunities(
        user_id=user_id,
        q="Python",
        category="Course",
        page=1,
        page_size=10
    )

    assert isinstance(res, PaginatedOpportunitySearchResultSchema)
    assert res.total == 1
    assert res.page == 1
    assert res.total_pages == 1
    assert len(res.items) == 1
    assert res.items[0].title == "Python Data Science"
