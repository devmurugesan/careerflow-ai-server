from abc import ABC, abstractmethod
from typing import List


class BaseStateEngine(ABC):
    """Abstract Base Class for Domain Opportunity State Engines."""

    @property
    @abstractmethod
    def valid_states(self) -> List[str]:
        """List of all valid state strings in topological order."""
        pass

    @abstractmethod
    def transition(self, current_state: str, new_state: str) -> str:
        """Evaluates state transition and returns validated new state."""
        pass


class CourseStateEngine(BaseStateEngine):
    """State Machine for Course Opportunities.
    States: Registered -> Started -> In Progress -> Assignment Pending -> Completed -> Certificate Available
    """

    STATES = [
        "Registered",
        "Started",
        "In Progress",
        "Assignment Pending",
        "Completed",
        "Certificate Available",
        "Certificate Received"
    ]

    # Map status aliases from AI extraction
    ALIAS_MAP = {
        "course registered": "Registered",
        "enrolled": "Registered",
        "assignment available": "Assignment Pending",
        "assignment due": "Assignment Pending",
        "week 1": "In Progress",
        "week 2": "In Progress",
        "certificate": "Certificate Available",
        "certificate issued": "Certificate Available",
        "completed": "Completed"
    }

    @property
    def valid_states(self) -> List[str]:
        return self.STATES

    def normalize_state(self, state: str) -> str:
        if not state:
            return "Registered"
        clean = state.strip().lower()
        if clean in self.ALIAS_MAP:
            return self.ALIAS_MAP[clean]
        for s in self.STATES:
            if s.lower() == clean:
                return s
        return state.title()

    def transition(self, current_state: str, new_state: str) -> str:
        curr_norm = self.normalize_state(current_state)
        new_norm = self.normalize_state(new_state)

        if not current_state or curr_norm not in self.STATES:
            if new_norm in self.STATES:
                return new_norm
            return "Registered"

        if new_norm not in self.STATES:
            return current_state

        curr_idx = self.STATES.index(curr_norm)
        new_idx = self.STATES.index(new_norm)

        # Retain highest forward progress
        if new_idx >= curr_idx:
            return new_norm

        return curr_norm
