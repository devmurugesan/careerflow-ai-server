from typing import List
from app.domain.engines.course_engine import BaseStateEngine


class GenericStateEngine(BaseStateEngine):
    """Flexible State Engine for Workshop, Webinar, Scholarship, Coding Contest, Assessment, Certification, and Unknown opportunities."""

    DEFAULT_STATES = [
        "Registered",
        "Invited",
        "Scheduled",
        "In Progress",
        "Submitted",
        "Completed",
        "Awarded"
    ]

    def __init__(self, states: List[str] = None):
        self._states = states or self.DEFAULT_STATES

    @property
    def valid_states(self) -> List[str]:
        return self._states

    def transition(self, current_state: str, new_state: str) -> str:
        if not new_state:
            return current_state or "Registered"
        if not current_state:
            return new_state

        curr_clean = current_state.strip().title()
        new_clean = new_state.strip().title()

        if curr_clean in self._states and new_clean in self._states:
            curr_idx = self._states.index(curr_clean)
            new_idx = self._states.index(new_clean)
            if new_idx >= curr_idx:
                return new_clean
            return curr_clean

        # Allow flexible transition for unlisted/unknown custom states
        return new_clean
