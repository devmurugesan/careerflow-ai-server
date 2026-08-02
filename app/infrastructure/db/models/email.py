import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, DateTime, ForeignKey, Float, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


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
