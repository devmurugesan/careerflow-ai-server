import pytest
from app.domain.engines.course_engine import CourseStateEngine
from app.domain.engines.company_engine import CompanyStateEngine
from app.domain.engines.hackathon_engine import HackathonStateEngine


def test_course_state_engine_forward_progression():
    engine = CourseStateEngine()
    
    assert engine.transition("Registered", "Started") == "Started"
    assert engine.transition("Started", "In Progress") == "In Progress"
    assert engine.transition("In Progress", "Completed") == "Completed"
    assert engine.transition("Completed", "Certificate Received") == "Certificate Received"


def test_course_state_engine_prevents_backward_regression():
    engine = CourseStateEngine()
    
    # Current progress is 'Completed'; an earlier email saying 'Started' should NOT regress state
    assert engine.transition("Completed", "Started") == "Completed"


def test_company_state_engine_terminal_rejection_lock():
    engine = CompanyStateEngine()
    
    assert engine.transition("Registered", "Assessment") == "Assessment"
    assert engine.transition("Assessment", "Interview") == "Interview"
    assert engine.transition("Interview", "Rejected") == "Rejected"
    
    # Once Rejected, subsequent updates cannot change state back to Offer
    assert engine.transition("Rejected", "Offer") == "Rejected"


def test_hackathon_state_engine_progression():
    engine = HackathonStateEngine()
    
    assert engine.transition("Registered", "Team Formation") == "Team Formation"
    assert engine.transition("Team Formation", "Idea Submission") == "Idea Submission"
    assert engine.transition("Idea Submission", "Final Round") == "Final Round"
    assert engine.transition("Final Round", "Completed") == "Completed"
