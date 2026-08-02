import uuid
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from app.domain.ai.schemas import AIExtractionResult, OpportunityCategory, EmailCategory, PriorityLevel
from app.domain.matching.matching_engine import OpportunityMatchingEngine
from app.domain.engines.course_engine import CourseStateEngine
from app.domain.engines.company_engine import CompanyStateEngine
from app.domain.engines.hackathon_engine import HackathonStateEngine
from app.domain.engines.generic_engine import GenericStateEngine
from app.services.opportunity_service import OpportunityService
from app.infrastructure.db.models import OpportunityTable, EmailTable, OpportunityEmailTable, OpportunityStatusHistoryTable


def test_matching_engine_thread_id_exact_match():
    engine = OpportunityMatchingEngine(threshold=0.65)

    source_email = MagicMock(spec=EmailTable)
    source_email.thread_id = "thread-12345"

    linked_email = MagicMock(spec=EmailTable)
    linked_email.thread_id = "thread-12345"

    email_link = MagicMock(spec=OpportunityEmailTable)
    email_link.email = linked_email

    opp = MagicMock(spec=OpportunityTable)
    opp.email_links = [email_link]

    extraction = AIExtractionResult(
        category=OpportunityCategory.COURSE,
        organization="Coursera",
        title="Python Data Structures",
        status="Registered",
        email_summary="Registered for Python course",
        confidence=0.95
    )

    best_match, score = engine.find_best_match(extraction, source_email, [opp])
    assert best_match == opp
    assert score == 1.0


def test_matching_engine_fuzzy_title_org_match():
    engine = OpportunityMatchingEngine(threshold=0.65)

    opp = MagicMock(spec=OpportunityTable)
    opp.category = "Course"
    opp.organization_or_platform = "Coursera Inc."
    opp.title = "Machine Learning Specialization"
    opp.email_links = []
    opp.extra_data = {}

    extraction = AIExtractionResult(
        category=OpportunityCategory.COURSE,
        organization="Coursera",
        title="Machine Learning Specialization Course",
        status="In Progress",
        email_summary="Week 2 assignment released",
        confidence=0.90
    )

    best_match, score = engine.find_best_match(extraction, None, [opp])
    assert best_match == opp
    assert score >= 0.65


def test_matching_engine_dissimilar_creates_new():
    engine = OpportunityMatchingEngine(threshold=0.65)

    opp = MagicMock(spec=OpportunityTable)
    opp.category = "Company Recruitment"
    opp.organization_or_platform = "Google"
    opp.title = "Software Engineer"
    opp.email_links = []
    opp.extra_data = {}

    extraction = AIExtractionResult(
        category=OpportunityCategory.COURSE,
        organization="Udemy",
        title="Full Stack Web Development",
        status="Registered",
        email_summary="Enrolled in web dev course",
        confidence=0.95
    )

    best_match, score = engine.find_best_match(extraction, None, [opp])
    assert best_match is None
    assert score < 0.65


def test_course_state_transitions():
    engine = CourseStateEngine()
    
    # Registered -> Started
    assert engine.transition("Registered", "Started") == "Started"
    
    # Started -> Assignment Pending
    assert engine.transition("Started", "Assignment Pending") == "Assignment Pending"

    # Forward progress lock (Completed -> Registered retains Completed)
    assert engine.transition("Completed", "Registered") == "Completed"

    # Alias normalization
    assert engine.normalize_state("enrolled") == "Registered"
    assert engine.normalize_state("certificate issued") == "Certificate Available"


def test_company_state_transitions():
    engine = CompanyStateEngine()

    # Registered -> Application Submitted -> Assessment Scheduled -> Interview Scheduled
    s1 = engine.transition("Registered", "Application Submitted")
    assert s1 == "Application Submitted"

    s2 = engine.transition(s1, "Assessment Scheduled")
    assert s2 == "Assessment Scheduled"

    s3 = engine.transition(s2, "Interview Scheduled")
    assert s3 == "Interview Scheduled"

    # Terminal state lock (Rejected lock)
    s4 = engine.transition(s3, "Rejected")
    assert s4 == "Rejected"

    s5 = engine.transition(s4, "Interview Scheduled")
    assert s5 == "Rejected"


def test_hackathon_state_transitions():
    engine = HackathonStateEngine()

    assert engine.transition("Registered", "Problem Statement Released") == "Problem Statement Released"
    assert engine.transition("Problem Statement Released", "Round 1") == "Round 1"
    assert engine.transition("Round 1", "Winner") == "Winner"


def test_generic_state_engine_unknown_states():
    engine = GenericStateEngine()

    assert engine.transition("Registered", "Custom State A") == "Custom State A"
    assert engine.transition(None, "Scheduled") == "Scheduled"


@pytest.mark.asyncio
async def test_duplicate_prevention_4_emails_1_opportunity():
    user_id = uuid.uuid4()
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()
    mock_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))

    thread_id = "thread-coursera-ml"
    service = OpportunityService(mock_session)

    extractions = [
        AIExtractionResult(
            category=OpportunityCategory.COURSE,
            organization="Coursera",
            title="Machine Learning Specialization",
            status="Registered",
            email_summary="Registration confirmed for ML course",
            confidence=0.98
        ),
        AIExtractionResult(
            category=OpportunityCategory.COURSE,
            organization="Coursera",
            title="Machine Learning Specialization",
            status="In Progress",
            email_summary="Week 1 lectures available",
            confidence=0.95
        ),
        AIExtractionResult(
            category=OpportunityCategory.COURSE,
            organization="Coursera",
            title="Machine Learning Specialization",
            status="Assignment Pending",
            email_summary="Week 2 Assignment due in 3 days",
            confidence=0.92
        ),
        AIExtractionResult(
            category=OpportunityCategory.COURSE,
            organization="Coursera",
            title="Machine Learning Specialization",
            status="Certificate Available",
            email_summary="Certificate of Completion issued",
            confidence=0.99
        )
    ]

    existing_opp = None
    all_candidates = []

    for idx, ext in enumerate(extractions):
        email = MagicMock(spec=EmailTable)
        email.id = uuid.uuid4()
        email.thread_id = thread_id
        email.subject = f"Coursera Update {idx+1}"
        email.snippet = ext.email_summary

        service.repo.get_user_candidate_opportunities = AsyncMock(return_value=all_candidates)

        opp = await service.process_ai_extraction(user_id, email, ext)
        assert opp is not None
        if existing_opp is None:
            existing_opp = opp
            all_candidates.append(opp)

        assert opp.id == existing_opp.id

    assert existing_opp.current_status == "Certificate Available"


@pytest.mark.asyncio
async def test_out_of_order_late_arriving_email():
    user_id = uuid.uuid4()
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()
    mock_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))

    service = OpportunityService(mock_session)

    existing_opp = OpportunityTable(
        id=uuid.uuid4(),
        user_id=user_id,
        category="Company Recruitment",
        title="Software Engineer",
        organization_or_platform="Zoho",
        current_status="Interview Scheduled",
        priority="HIGH",
        confidence_score=0.95,
        is_archived=False,
        email_links=[]
    )

    late_email = MagicMock(spec=EmailTable)
    late_email.id = uuid.uuid4()
    late_email.thread_id = "thread-zoho-1"
    late_email.subject = "Application Received - Zoho"
    late_email.snippet = "Your application for Software Engineer has been received."

    ext = AIExtractionResult(
        category=OpportunityCategory.COMPANY_RECRUITMENT,
        organization="Zoho",
        title="Software Engineer",
        status="Application Submitted",
        email_summary="Application received email",
        confidence=0.90
    )

    service.repo.get_user_candidate_opportunities = AsyncMock(return_value=[existing_opp])

    opp = await service.process_ai_extraction(user_id, late_email, ext)
    assert opp.id == existing_opp.id
    assert opp.current_status == "Interview Scheduled"


@pytest.mark.asyncio
async def test_low_confidence_ai_extraction_handling():
    user_id = uuid.uuid4()
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()
    mock_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))

    service = OpportunityService(mock_session)

    email = MagicMock(spec=EmailTable)
    email.id = uuid.uuid4()
    email.thread_id = "thread-low-conf"
    email.subject = "Possible Opportunity Update"
    email.snippet = "Ambiguous promotional email"

    ext = AIExtractionResult(
        category=OpportunityCategory.UNKNOWN,
        organization="Unclear",
        title="Potential Event",
        status="Registered",
        email_summary="Low confidence summary",
        confidence=0.35
    )

    service.repo.get_user_candidate_opportunities = AsyncMock(return_value=[])

    opp = await service.process_ai_extraction(user_id, email, ext)
    assert opp is not None
    assert opp.confidence_score == 0.35
    assert opp.extra_data.get("is_low_confidence") is True


@pytest.mark.asyncio
async def test_timeline_generation():
    user_id = uuid.uuid4()
    opp_id = uuid.uuid4()
    mock_session = AsyncMock()

    service = OpportunityService(mock_session)

    hist1 = OpportunityStatusHistoryTable(
        id=uuid.uuid4(),
        opportunity_id=opp_id,
        source_email_id=uuid.uuid4(),
        from_status="Created",
        to_status="Registered",
        reason_summary="Course Registered",
        changed_at=datetime.now(timezone.utc)
    )

    opp = OpportunityTable(
        id=opp_id,
        user_id=user_id,
        category="Course",
        title="Python Data Science",
        organization_or_platform="Coursera",
        current_status="Registered",
        summary="Course Registered",
        confidence_score=0.95,
        status_history=[hist1],
        email_links=[]
    )

    service.repo.get_by_id = AsyncMock(return_value=opp)

    timeline = await service.get_opportunity_timeline(user_id, opp_id)
    assert timeline is not None
    assert len(timeline) == 1
    assert timeline[0]["from_status"] == "Created"
    assert timeline[0]["to_status"] == "Registered"
