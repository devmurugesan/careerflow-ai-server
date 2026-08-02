import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.domain.ai.schemas import AIExtractionResult, EmailCategory, OpportunityCategory
from app.domain.matching.matching_engine import OpportunityMatchingEngine
from app.domain.engines.course_engine import CourseStateEngine
from app.domain.engines.company_engine import CompanyStateEngine
from app.domain.engines.hackathon_engine import HackathonStateEngine
from app.domain.engines.generic_engine import GenericStateEngine
from app.infrastructure.db.models import (
    OpportunityTable,
    OpportunityEmailTable,
    OpportunityStatusHistoryTable,
    ReminderTable,
    EmailTable
)
from app.infrastructure.db.repositories.opportunity_repo import OpportunityRepository
from app.core.logger import logger


class OpportunityService:
    """Service orchestrating entity deduplication via matching engine, state transitions, timeline, and history logs."""

    LOW_CONFIDENCE_THRESHOLD = 0.40

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = OpportunityRepository(session)
        self.matching_engine = OpportunityMatchingEngine(threshold=0.65)

    def _get_engine(self, category: str):
        cat_lower = category.lower() if category else ""
        if cat_lower == "course" or cat_lower == "certification":
            return CourseStateEngine()
        elif any(c in cat_lower for c in ["company", "recruitment", "interview", "assessment", "internship"]):
            return CompanyStateEngine()
        elif "hackathon" in cat_lower or "contest" in cat_lower:
            return HackathonStateEngine()
        return GenericStateEngine()

    async def process_ai_extraction(
        self,
        user_id: uuid.UUID,
        email: EmailTable,
        extraction: AIExtractionResult
    ) -> Optional[OpportunityTable]:
        """Core pipeline processing extracted AI data into existing or new opportunity via matching engine."""
        ext_cat_str = extraction.category.value if hasattr(extraction.category, 'value') else str(extraction.category)
        if ext_cat_str in ["Ignore", "REMINDER", "Ignore/Newsletter"]:
            return None

        # Check for Low Confidence score
        confidence = getattr(extraction, 'confidence', None)
        if confidence is None:
            confidence = getattr(extraction, 'confidence_score', 1.0)

        is_low_confidence = confidence < self.LOW_CONFIDENCE_THRESHOLD
        if is_low_confidence:
            logger.warning(
                "Processing low confidence AI extraction",
                user_id=str(user_id),
                email_id=str(email.id),
                confidence=confidence
            )

        # 1. Matching Engine across user candidates
        candidates = await self.repo.get_user_candidate_opportunities(user_id)
        matched_opp, match_score = self.matching_engine.find_best_match(extraction, email, candidates)

        # Extraction fields
        title = getattr(extraction, 'title', None) or getattr(extraction, 'opportunity_title', None) or "Untitled Opportunity"
        org = getattr(extraction, 'organization', None) or getattr(extraction, 'platform_or_company', None) or "Unknown Organization"
        status_extracted = getattr(extraction, 'status', None) or getattr(extraction, 'current_status', None) or "Registered"
        summary = getattr(extraction, 'email_summary', None) or getattr(extraction, 'summary', None) or email.snippet

        engine = self._get_engine(ext_cat_str)

        if matched_opp:
            old_status = matched_opp.current_status
            new_status = engine.transition(old_status, status_extracted) if engine else status_extracted

            # State transition & progress update
            matched_opp.current_status = new_status
            if extraction.deadline:
                matched_opp.deadline = extraction.deadline
            if extraction.event_date:
                matched_opp.event_date = extraction.event_date
            if extraction.action_required:
                matched_opp.action_required = extraction.action_required
            matched_opp.summary = summary
            matched_opp.confidence_score = confidence
            matched_opp.updated_at = datetime.now(timezone.utc)

            # Audit History Log (Always record every incoming email update)
            history_log = OpportunityStatusHistoryTable(
                opportunity_id=matched_opp.id,
                source_email_id=email.id,
                from_status=old_status,
                to_status=new_status,
                reason_summary=f"[{'Low-Confidence ' if is_low_confidence else ''}Update from '{email.subject}']: {summary}"
            )
            self.session.add(history_log)
            target_opportunity = matched_opp
        else:
            # Create new Opportunity
            target_opportunity = OpportunityTable(
                user_id=user_id,
                category=ext_cat_str,
                title=title,
                organization_or_platform=org,
                current_status=status_extracted,
                priority=getattr(extraction, 'priority', 'MEDIUM') if isinstance(getattr(extraction, 'priority', 'MEDIUM'), str) else getattr(extraction, 'priority', 'MEDIUM').value,
                deadline=extraction.deadline,
                event_date=extraction.event_date,
                action_required=extraction.action_required,
                summary=summary,
                confidence_score=confidence,
                extra_data={
                    "registration_id": getattr(extraction, 'registration_id', None),
                    "is_low_confidence": is_low_confidence
                }
            )
            self.session.add(target_opportunity)
            await self.session.flush()

            # Audit History initial entry
            history_log = OpportunityStatusHistoryTable(
                opportunity_id=target_opportunity.id,
                source_email_id=email.id,
                from_status="Created",
                to_status=status_extracted,
                reason_summary=f"Created from '{email.subject}': {summary}"
            )
            self.session.add(history_log)

        # 4. Link Email to Opportunity (Prevent duplicate links)
        stmt_link_check = select(OpportunityEmailTable).where(
            and_(
                OpportunityEmailTable.opportunity_id == target_opportunity.id,
                OpportunityEmailTable.email_id == email.id
            )
        )
        existing_link = (await self.session.execute(stmt_link_check)).scalar_one_or_none()
        if not existing_link:
            link = OpportunityEmailTable(
                opportunity_id=target_opportunity.id,
                email_id=email.id,
                extracted_status=status_extracted
            )
            self.session.add(link)

        # 5. Generate Deadline Reminder if present
        if extraction.deadline:
            reminder = ReminderTable(
                user_id=user_id,
                opportunity_id=target_opportunity.id,
                title=f"Deadline: {target_opportunity.title} ({target_opportunity.organization_or_platform})",
                trigger_at=extraction.deadline,
                status="PENDING"
            )
            self.session.add(reminder)

        await self.session.flush()
        return target_opportunity

    async def get_opportunity_timeline(
        self, user_id: uuid.UUID, opportunity_id: uuid.UUID
    ) -> Optional[List[Dict[str, Any]]]:
        """Generates chronological event timeline for an opportunity."""
        opportunity = await self.repo.get_by_id(opportunity_id)
        if not opportunity or opportunity.user_id != user_id:
            return None

        timeline = []
        for history in opportunity.status_history:
            source_email = None
            if opportunity.email_links:
                for link in opportunity.email_links:
                    if link.email and link.email.id == history.source_email_id:
                        source_email = link.email
                        break

            timeline.append({
                "id": str(history.id),
                "timestamp": history.changed_at.isoformat() if history.changed_at else datetime.now(timezone.utc).isoformat(),
                "event_type": "STATE_TRANSITION" if history.from_status != history.to_status else "EMAIL_UPDATE",
                "from_status": history.from_status,
                "to_status": history.to_status,
                "summary": history.reason_summary or opportunity.summary,
                "email_subject": source_email.subject if source_email else "Automated Update",
                "source_email_id": str(history.source_email_id) if history.source_email_id else None,
                "action_required": opportunity.action_required
            })

        # Sort timeline in chronological order
        timeline.sort(key=lambda x: x["timestamp"])
        return timeline
