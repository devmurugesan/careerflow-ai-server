from typing import List
from app.domain.engines.course_engine import BaseStateEngine


class CompanyStateEngine(BaseStateEngine):
    """State Machine for Company Job Applications & Recruitment.
    Pipeline: Registered -> Application Submitted -> Assessment -> Assessment Scheduled -> Assessment Completed -> Interview -> Interview Scheduled -> Interview Completed -> Selected -> Offer Received -> Joined
    Terminal Failure States: Rejected, Withdrawn
    """

    PIPELINE_STATES = [
        "Registered",
        "Application Submitted",
        "Assessment",
        "Assessment Scheduled",
        "Assessment Pending",
        "Assessment Completed",
        "Interview",
        "Interview Scheduled",
        "Interview Completed",
        "Selected",
        "Offer Received",
        "Joined"
    ]

    TERMINAL_STATES = ["Rejected", "Withdrawn"]

    ALIAS_MAP = {
        "applied": "Application Submitted",
        "application received": "Application Submitted",
        "assessment invited": "Assessment Scheduled",
        "assessment pending": "Assessment Pending",
        "test scheduled": "Assessment Scheduled",
        "interview invited": "Interview Scheduled",
        "interview round 1": "Interview Scheduled",
        "interview round 2": "Interview Scheduled",
        "shortlisted": "Selected",
        "hired": "Joined",
        "offer letter": "Offer Received"
    }

    @property
    def valid_states(self) -> List[str]:
        return self.PIPELINE_STATES + self.TERMINAL_STATES

    def normalize_state(self, state: str) -> str:
        if not state:
            return "Registered"
        clean = state.strip().lower()
        if clean in self.ALIAS_MAP:
            return self.ALIAS_MAP[clean]
        for s in self.valid_states:
            if s.lower() == clean:
                return s
        return state.title()

    def transition(self, current_state: str, new_state: str) -> str:
        curr_norm = self.normalize_state(current_state)
        new_norm = self.normalize_state(new_state)

        if not current_state or curr_norm not in self.valid_states:
            if new_norm in self.valid_states:
                return new_norm
            return "Registered"

        # Terminal state lock
        if curr_norm in self.TERMINAL_STATES:
            return curr_norm

        if new_norm in self.TERMINAL_STATES:
            return new_norm

        if new_norm not in self.PIPELINE_STATES:
            return current_state

        curr_idx = self.PIPELINE_STATES.index(curr_norm) if curr_norm in self.PIPELINE_STATES else 0
        new_idx = self.PIPELINE_STATES.index(new_norm)

        if new_idx >= curr_idx:
            return new_norm

        return curr_norm
