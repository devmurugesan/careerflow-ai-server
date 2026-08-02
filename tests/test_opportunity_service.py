import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

from app.domain.ai.schemas import AIExtractionResult, EmailCategory, PriorityLevel
from app.infrastructure.db.models import EmailTable, OpportunityTable
from app.services.opportunity_service import OpportunityService


def test_ai_extraction_result_mapping():
    extraction = AIExtractionResult(
        category=EmailCategory.COMPANY,
        platform_or_company="Amazon",
        opportunity_title="SDE Intern",
        current_status="Assessment",
        priority=PriorityLevel.HIGH,
        deadline=datetime.now(timezone.utc),
        action_required="Complete online assessment link",
        summary="Amazon sent Online Assessment 1"
    )

    assert extraction.category == EmailCategory.COMPANY
    assert extraction.platform_or_company == "Amazon"
    assert extraction.current_status == "Assessment"
    assert extraction.action_required == "Complete online assessment link"
