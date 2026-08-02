import pytest
from datetime import datetime
from app.domain.ai.schemas import AIExtractionResult, EmailCategory, PriorityLevel


def test_ai_extraction_schema_valid_json_parsing():
    raw_json = """
    {
        "category": "Company",
        "platform_or_company": "Google",
        "opportunity_title": "Software Engineer, Backend",
        "current_status": "Interview",
        "priority": "HIGH",
        "deadline": "2026-08-15T18:00:00Z",
        "event_date": "2026-08-10T14:00:00Z",
        "action_required": "Confirm interview time slot via calendar link",
        "summary": "Google has invited you for a Technical Screen interview round.",
        "confidence_score": 0.98
    }
    """
    
    result = AIExtractionResult.model_validate_json(raw_json)
    
    assert result.category == EmailCategory.COMPANY
    assert result.platform_or_company == "Google"
    assert result.opportunity_title == "Software Engineer, Backend"
    assert result.current_status == "Interview"
    assert result.priority == PriorityLevel.HIGH
    assert result.confidence_score == 0.98
