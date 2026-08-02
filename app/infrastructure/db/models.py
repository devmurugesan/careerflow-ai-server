import uuid
from datetime import datetime, timezone
from typing import Optional, List, Any
from sqlalchemy import String, Boolean, DateTime, ForeignKey, BigInteger, Text, Float, UniqueConstraint, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class UserTable(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    google_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True, nullable=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    credentials: Mapped[Optional["GoogleCredentialTable"]] = relationship("GoogleCredentialTable", back_populates="user", uselist=False, cascade="all, delete-orphan")
    emails: Mapped[List["EmailTable"]] = relationship("EmailTable", back_populates="user", cascade="all, delete-orphan")
    opportunities: Mapped[List["OpportunityTable"]] = relationship("OpportunityTable", back_populates="user", cascade="all, delete-orphan")


class GoogleCredentialTable(Base):
    __tablename__ = "google_credentials"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    encrypted_access_token: Mapped[str] = mapped_column(Text, nullable=False)
    encrypted_refresh_token: Mapped[str] = mapped_column(Text, nullable=False)
    token_uri: Mapped[str] = mapped_column(String(255), nullable=False)
    client_id: Mapped[str] = mapped_column(String(255), nullable=False)
    scopes: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    history_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    is_connected: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user: Mapped["UserTable"] = relationship("UserTable", back_populates="credentials")


class EmailTable(Base):
    __tablename__ = "emails"
    __table_args__ = (
        UniqueConstraint("user_id", "gmail_message_id", name="uq_user_gmail_message"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    gmail_message_id: Mapped[str] = mapped_column(String(128), nullable=False)
    thread_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    sender: Mapped[str] = mapped_column(String(255), nullable=False)
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(Text, nullable=False)
    snippet: Mapped[str] = mapped_column(Text, nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    processing_status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    classified_category: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    raw_body_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped["UserTable"] = relationship("UserTable", back_populates="emails")
    opportunity_links: Mapped[List["OpportunityEmailTable"]] = relationship("OpportunityEmailTable", back_populates="email", cascade="all, delete-orphan")


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
    extra_data: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user: Mapped["UserTable"] = relationship("UserTable", back_populates="opportunities")
    email_links: Mapped[List["OpportunityEmailTable"]] = relationship("OpportunityEmailTable", back_populates="opportunity", cascade="all, delete-orphan")
    status_history: Mapped[List["OpportunityStatusHistoryTable"]] = relationship("OpportunityStatusHistoryTable", back_populates="opportunity", cascade="all, delete-orphan")
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
    linked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    opportunity: Mapped["OpportunityTable"] = relationship("OpportunityTable", back_populates="email_links")
    email: Mapped["EmailTable"] = relationship("EmailTable", back_populates="opportunity_links")


class OpportunityStatusHistoryTable(Base):
    __tablename__ = "opportunity_status_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    opportunity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id", ondelete="CASCADE"), index=True, nullable=False)
    source_email_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("emails.id", ondelete="SET NULL"), nullable=True)
    from_status: Mapped[str] = mapped_column(String(64), nullable=False)
    to_status: Mapped[str] = mapped_column(String(64), nullable=False)
    reason_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    opportunity: Mapped["OpportunityTable"] = relationship("OpportunityTable", back_populates="status_history")


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


class ReminderTable(Base):
    __tablename__ = "reminders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    opportunity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    trigger_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", index=True, nullable=False)
    channel: Mapped[str] = mapped_column(String(32), default="IN_APP", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    opportunity: Mapped["OpportunityTable"] = relationship("OpportunityTable", back_populates="reminders")
