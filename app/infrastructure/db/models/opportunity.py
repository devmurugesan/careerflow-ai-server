import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, DateTime, ForeignKey, Float, Text, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class OpportunityTable(Base):
    __tablename__ = "opportunities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    organization_or_platform: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    current_status: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(16), default="MEDIUM", nullable=False)
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    event_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    action_required: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user: Mapped["UserTable"] = relationship("UserTable", back_populates="opportunities")
    email_links: Mapped[List["OpportunityEmailTable"]] = relationship("OpportunityEmailTable", back_populates="opportunity", cascade="all, delete-orphan")
    course_detail: Mapped[Optional["CourseTable"]] = relationship("CourseTable", back_populates="opportunity", uselist=False, cascade="all, delete-orphan")
    company_detail: Mapped[Optional["CompanyApplicationTable"]] = relationship("CompanyApplicationTable", back_populates="opportunity", uselist=False, cascade="all, delete-orphan")
    hackathon_detail: Mapped[Optional["HackathonTable"]] = relationship("HackathonTable", back_populates="opportunity", uselist=False, cascade="all, delete-orphan")
    reminders: Mapped[List["ReminderTable"]] = relationship("ReminderTable", back_populates="opportunity", cascade="all, delete-orphan")


class OpportunityEmailTable(Base):
    __tablename__ = "opportunity_emails"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    opportunity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id", ondelete="CASCADE"), index=True, nullable=False)
    email_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("emails.id", ondelete="CASCADE"), index=True, nullable=False)
    extracted_status: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    opportunity: Mapped["OpportunityTable"] = relationship("OpportunityTable", back_populates="email_links")
    email: Mapped["EmailTable"] = relationship("EmailTable", back_populates="opportunity_links")


class CourseTable(Base):
    __tablename__ = "courses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    opportunity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id", ondelete="CASCADE"), unique=True, nullable=False)
    platform_name: Mapped[str] = mapped_column(String(255), nullable=False)
    course_name: Mapped[str] = mapped_column(String(255), nullable=False)
    instructor: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    completion_percentage: Mapped[int] = mapped_column(Integer, default=0)
    certificate_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    opportunity: Mapped["OpportunityTable"] = relationship("OpportunityTable", back_populates="course_detail")


class CompanyApplicationTable(Base):
    __tablename__ = "company_applications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    opportunity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id", ondelete="CASCADE"), unique=True, nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role_title: Mapped[str] = mapped_column(String(255), nullable=False)
    application_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    salary_range: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    opportunity: Mapped["OpportunityTable"] = relationship("OpportunityTable", back_populates="company_detail")


class HackathonTable(Base):
    __tablename__ = "hackathons"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    opportunity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id", ondelete="CASCADE"), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    team_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    submission_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    prize_pool: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    opportunity: Mapped["OpportunityTable"] = relationship("OpportunityTable", back_populates="hackathon_detail")
