from typing import List
from app.domain.engines.course_engine import BaseStateEngine


class HackathonStateEngine(BaseStateEngine):
    """State Machine for Hackathon & Coding Contest Opportunities.
    States: Registered -> Team Formation -> Problem Statement Released -> Idea Submission -> Prototype -> Round 1 -> Round 2 -> Final Round -> Finalist -> Winner -> Completed
    """

    STATES = [
        "Registered",
        "Team Formation",
        "Problem Statement Released",
        "Idea Submission",
        "Prototype",
        "Round 1",
        "Round 2",
        "Final Round",
        "Finalist",
        "Winner",
        "Completed"
    ]

    ALIAS_MAP = {
        "registered": "Registered",
        "team formation": "Team Formation",
        "problem statement": "Problem Statement Released",
        "submission open": "Idea Submission",
        "round 1": "Round 1",
        "round 2": "Round 2",
        "final round": "Final Round",
        "finalist": "Finalist",
        "winner": "Winner",
        "won": "Winner"
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

        if new_idx >= curr_idx:
            return new_norm

        return curr_norm
