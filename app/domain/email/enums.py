from enum import Enum


class OpportunityCategory(str, Enum):
    COURSE = "Course"
    CERTIFICATE = "Certificate"
    CERTIFICATION = "Certification"
    COMPANY = "Company"
    COMPANY_RECRUITMENT = "Company Recruitment"
    INTERNSHIP = "Internship"
    HACKATHON = "Hackathon"
    WORKSHOP = "Workshop"
    WEBINAR = "Webinar"
    SCHOLARSHIP = "Scholarship"
    CODING_CONTEST = "Coding Contest"
    ASSESSMENT = "Assessment"
    UNKNOWN = "Unknown"

    @classmethod
    def _missing_(cls, value: object):
        if isinstance(value, str):
            val_lower = value.strip().lower()
            mapping = {
                "course": cls.COURSE,
                "certification": cls.CERTIFICATION,
                "certificate": cls.CERTIFICATE,
                "company recruitment": cls.COMPANY_RECRUITMENT,
                "company": cls.COMPANY,
                "recruitment": cls.COMPANY_RECRUITMENT,
                "interview": cls.COMPANY,
                "internship": cls.INTERNSHIP,
                "hackathon": cls.HACKATHON,
                "workshop": cls.WORKSHOP,
                "webinar": cls.WEBINAR,
                "scholarship": cls.SCHOLARSHIP,
                "coding contest": cls.CODING_CONTEST,
                "contest": cls.CODING_CONTEST,
                "assessment": cls.ASSESSMENT,
                "unknown": cls.UNKNOWN,
                "event": cls.WORKSHOP,
                "ignore": cls.UNKNOWN,
                "reminder": cls.UNKNOWN,
            }
            if val_lower in mapping:
                return mapping[val_lower]
        return cls.UNKNOWN


class EmailCategory(str, Enum):
    COURSE = "Course"
    CERTIFICATE = "Certificate"
    CERTIFICATION = "Certification"
    COMPANY = "Company"
    COMPANY_RECRUITMENT = "Company Recruitment"
    ASSESSMENT = "Assessment"
    INTERVIEW = "Interview"
    HACKATHON = "Hackathon"
    INTERNSHIP = "Internship"
    EVENT = "Event"
    WORKSHOP = "Workshop"
    WEBINAR = "Webinar"
    SCHOLARSHIP = "Scholarship"
    CODING_CONTEST = "Coding Contest"
    UNKNOWN = "Unknown"
    REMINDER = "Reminder"
    IGNORE = "Ignore"


class PriorityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class ProcessingStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"
    IGNORED = "IGNORED"
