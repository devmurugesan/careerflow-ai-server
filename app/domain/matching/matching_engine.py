import re
from typing import Optional, List, Tuple
from difflib import SequenceMatcher
from app.domain.ai.schemas import AIExtractionResult, OpportunityCategory
from app.infrastructure.db.models import OpportunityTable, EmailTable


class OpportunityMatchingEngine:
    """Weighted multi-signal matching engine for opportunity deduplication."""

    THREAD_WEIGHT = 1.0
    TITLE_WEIGHT = 0.40
    ORG_WEIGHT = 0.35
    CATEGORY_WEIGHT = 0.15
    EXTRA_ID_WEIGHT = 0.10

    MATCH_THRESHOLD = 0.65

    def __init__(self, threshold: float = 0.65):
        self.threshold = threshold

    def _normalize_string(self, text: Optional[str]) -> str:
        if not text:
            return ""
        cleaned = re.sub(r'(?i)\b(inc|llc|ltd|pvt|corp|corporation|co|platform|course|specialization|program|hiring|recruitment|assessment|hackathon)\b', '', text)
        cleaned = re.sub(r'[^a-zA-Z0-9\s]', ' ', cleaned)
        return ' '.join(cleaned.lower().split())

    def calculate_similarity(self, str1: Optional[str], str2: Optional[str]) -> float:
        norm1 = self._normalize_string(str1)
        norm2 = self._normalize_string(str2)
        if not norm1 or not norm2:
            return 0.0
        if norm1 == norm2:
            return 1.0
        if norm1 in norm2 or norm2 in norm1:
            return 0.85
        return SequenceMatcher(None, norm1, norm2).ratio()

    def find_best_match(
        self,
        extraction: AIExtractionResult,
        source_email: Optional[EmailTable],
        candidates: List[OpportunityTable]
    ) -> Tuple[Optional[OpportunityTable], float]:
        if not candidates:
            return None, 0.0

        best_candidate: Optional[OpportunityTable] = None
        best_score: float = 0.0

        for opp in candidates:
            if source_email and source_email.thread_id and opp.email_links:
                for link in opp.email_links:
                    if link.email and link.email.thread_id == source_email.thread_id:
                        return opp, 1.0

            score = 0.0
            ext_category = extraction.category.value if hasattr(extraction.category, 'value') else str(extraction.category)
            if opp.category == ext_category:
                score += self.CATEGORY_WEIGHT
            elif opp.category in ["Course", "Certification"] and ext_category in ["Course", "Certification"]:
                score += self.CATEGORY_WEIGHT * 0.8
            elif opp.category in ["Company Recruitment", "Company", "Internship", "Assessment"] and ext_category in ["Company Recruitment", "Company", "Internship", "Assessment"]:
                score += self.CATEGORY_WEIGHT * 0.8

            ext_org = getattr(extraction, 'organization', None) or getattr(extraction, 'platform_or_company', None) or ""
            org_sim = self.calculate_similarity(ext_org, opp.organization_or_platform)
            score += (org_sim * self.ORG_WEIGHT)

            ext_title = getattr(extraction, 'title', None) or getattr(extraction, 'opportunity_title', None) or ""
            title_sim = self.calculate_similarity(ext_title, opp.title)
            score += (title_sim * self.TITLE_WEIGHT)

            if opp.extra_data and isinstance(opp.extra_data, dict):
                opp_reg_id = opp.extra_data.get("registration_id") or opp.extra_data.get("application_id")
                ext_reg_id = getattr(extraction, 'registration_id', None)
                if opp_reg_id and ext_reg_id and str(opp_reg_id).lower() == str(ext_reg_id).lower():
                    score += self.EXTRA_ID_WEIGHT

            if score > best_score:
                best_score = score
                best_candidate = opp

        if best_score >= self.threshold:
            return best_candidate, round(best_score, 3)

        return None, round(best_score, 3)
