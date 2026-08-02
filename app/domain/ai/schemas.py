from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from app.domain.email.enums import EmailCategory, OpportunityCategory, PriorityLevel


class AIExtractionResult(BaseModel):
    """Structured Pydantic schema returned by LLM Provider abstraction for opportunity extraction."""
    category: OpportunityCategory = Field(
        default=OpportunityCategory.UNKNOWN,
        description="Classified opportunity category: Course, Certification, Company Recruitment, Internship, Hackathon, Workshop, Webinar, Scholarship, Coding Contest, Assessment, Unknown"
    )
    organization: Optional[str] = Field(
        default=None,
        description="Name of the hosting platform, issuing organization, or hiring company (e.g. Coursera, Google, HackerRank)"
    )
    platform_or_company: Optional[str] = Field(
        default=None,
        description="Alias for organization name"
    )
    title: Optional[str] = Field(
        default=None,
        description="Name of the course, job role, hackathon title, or assessment name"
    )
    opportunity_title: Optional[str] = Field(
        default=None,
        description="Alias for opportunity title"
    )
    status: Optional[str] = Field(
        default=None,
        description="Current status string extracted from email (e.g. Registered, Submitted, Assessment Scheduled, Certificate Available)"
    )
    current_status: Optional[str] = Field(
        default=None,
        description="Alias for extracted status"
    )
    priority: PriorityLevel = Field(
        default=PriorityLevel.MEDIUM,
        description="Assigned priority level: LOW, MEDIUM, HIGH, URGENT"
    )
    deadline: Optional[datetime] = Field(
        default=None,
        description="ISO datetime string for application, assessment, or submission deadline if present"
    )
    event_date: Optional[datetime] = Field(
        default=None,
        description="ISO datetime string for scheduled interview or event if present"
    )
    registration_date: Optional[datetime] = Field(
        default=None,
        description="ISO datetime string for registration if present"
    )
    certificate_available: Optional[bool] = Field(
        default=None,
        description="True if certificate is issued or available for download"
    )
    progress_percentage: Optional[float] = Field(
        default=None,
        description="Progress percentage from 0.0 to 100.0 if present"
    )
    action_required: Optional[str] = Field(
        default=None,
        description="Short description of specific next action required from the user"
    )
    email_summary: Optional[str] = Field(
        default=None,
        description="Max 40-word clear summary of the update contained in the email"
    )
    summary: Optional[str] = Field(
        default=None,
        description="Alias for email summary"
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score of AI extraction from 0.0 to 1.0"
    )
    confidence_score: Optional[float] = Field(
        default=None,
        description="Alias for confidence score"
    )
    reasoning: Optional[str] = Field(
        default=None,
        description="Internal debugging rationale, not shown to frontend"
    )

    @field_validator('platform_or_company', mode='before')
    def sync_org(cls, v, info):
        return v or info.data.get('organization')

    @field_validator('organization', mode='before')
    def sync_org_alias(cls, v, info):
        return v or info.data.get('platform_or_company')

    @field_validator('opportunity_title', mode='before')
    def sync_title(cls, v, info):
        return v or info.data.get('title')

    @field_validator('title', mode='before')
    def sync_title_alias(cls, v, info):
        return v or info.data.get('opportunity_title')

    @field_validator('current_status', mode='before')
    def sync_status(cls, v, info):
        return v or info.data.get('status')

    @field_validator('status', mode='before')
    def sync_status_alias(cls, v, info):
        return v or info.data.get('current_status')

    @field_validator('summary', mode='before')
    def sync_summary(cls, v, info):
        return v or info.data.get('email_summary')

    @field_validator('email_summary', mode='before')
    def sync_summary_alias(cls, v, info):
        return v or info.data.get('summary')

    @field_validator('confidence_score', mode='before')
    def sync_confidence(cls, v, info):
        return v if v is not None else info.data.get('confidence', 1.0)
