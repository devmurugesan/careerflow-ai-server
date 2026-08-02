from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class CategorySummary(BaseModel):
    total: int = 0
    active: int = 0
    completed: int = 0
    certificates_ready: int = 0


class CompanySummary(BaseModel):
    applications: int = 0
    assessments: int = 0
    interviews: int = 0
    offers: int = 0


class HackathonSummary(BaseModel):
    registered: int = 0
    active: int = 0
    completed: int = 0


class SingleCountSummary(BaseModel):
    active: int = 0


class OverallSummary(BaseModel):
    total_opportunities: int = 0
    active: int = 0
    completed: int = 0


class DashboardSummarySchema(BaseModel):
    courses: CategorySummary
    companies: CompanySummary
    hackathons: HackathonSummary
    internships: SingleCountSummary
    scholarships: SingleCountSummary
    coding_contests: SingleCountSummary
    overall: OverallSummary


class UpcomingOpportunitySchema(BaseModel):
    id: str
    title: str
    category: str
    organization: str
    current_state: str
    deadline: datetime
    days_remaining: int
    priority: str


class RecentActivitySchema(BaseModel):
    id: str
    title: str
    category: str
    organization: str
    new_state: str
    previous_state: str
    updated_at: datetime
    summary: Optional[str] = None


class CourseOpportunityItemSchema(BaseModel):
    id: str
    title: str
    organization: str
    current_state: str
    progress_percentage: float = 0.0
    certificate_ready: bool = False
    updated_at: datetime


class CoursesDashboardSchema(BaseModel):
    active_courses: List[CourseOpportunityItemSchema] = []
    completed_courses: List[CourseOpportunityItemSchema] = []
    certificates_ready: List[CourseOpportunityItemSchema] = []
    average_progress_percentage: float = 0.0
    timeline_summary: List[Dict[str, Any]] = []


class CompanyOpportunityItemSchema(BaseModel):
    id: str
    title: str
    organization: str
    current_state: str
    priority: str
    deadline: Optional[datetime] = None
    event_date: Optional[datetime] = None
    action_required: Optional[str] = None
    updated_at: datetime


class CompaniesDashboardSchema(BaseModel):
    applied: List[CompanyOpportunityItemSchema] = []
    assessment: List[CompanyOpportunityItemSchema] = []
    interview: List[CompanyOpportunityItemSchema] = []
    offer: List[CompanyOpportunityItemSchema] = []
    rejected: List[CompanyOpportunityItemSchema] = []
    joined: List[CompanyOpportunityItemSchema] = []


class HackathonOpportunityItemSchema(BaseModel):
    id: str
    title: str
    organization: str
    current_state: str
    deadline: Optional[datetime] = None
    event_date: Optional[datetime] = None
    updated_at: datetime


class HackathonsDashboardSchema(BaseModel):
    registered: List[HackathonOpportunityItemSchema] = []
    round_1: List[HackathonOpportunityItemSchema] = []
    round_2: List[HackathonOpportunityItemSchema] = []
    finalist: List[HackathonOpportunityItemSchema] = []
    winner: List[HackathonOpportunityItemSchema] = []
    completed: List[HackathonOpportunityItemSchema] = []


class CertificateItemSchema(BaseModel):
    id: str
    title: str
    organization: str
    completion_date: datetime
    certificate_status: str
    certificate_url: Optional[str] = None


class OpportunitySearchItemSchema(BaseModel):
    id: str
    category: str
    title: str
    organization: str
    current_state: str
    priority: str
    deadline: Optional[datetime] = None
    event_date: Optional[datetime] = None
    summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class PaginatedOpportunitySearchResultSchema(BaseModel):
    items: List[OpportunitySearchItemSchema]
    total: int
    page: int
    page_size: int
    total_pages: int
