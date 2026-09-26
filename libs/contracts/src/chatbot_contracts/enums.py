"""Closed sets of values used across contracts."""

from enum import StrEnum


class SourceType(StrEnum):
    TEXTBOOK = "textbook"
    LECTURE_NOTE = "lecture_note"
    PAST_EXAM = "past_exam"
    ANSWER_KEY = "answer_key"
    EXTERNAL_EXERCISE = "external_exercise"


class RegionKind(StrEnum):
    TEXT = "text"
    FIGURE = "figure"
    SCAN = "scan"
    TABLE = "table"
    EQUATION = "equation"
    CODE = "code"


class KnowledgeBaseStatus(StrEnum):
    CANDIDATE = "candidate"
    PUBLISHED = "published"
    REJECTED = "rejected"


class CleanOrigin(StrEnum):
    QUESTION = "question"
    UPLOAD = "upload"
    EXTERNAL = "external"


class CodeLanguage(StrEnum):
    R = "r"
    PYTHON = "python"
    EXCEL = "excel"


class Verdict(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"


class ConfidenceLevel(StrEnum):
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"


class EscalationStatus(StrEnum):
    OPEN = "open"
    EXTERNAL_ANSWERED = "external_answered"
    EXPERT_NOTIFIED = "expert_notified"
    EXPERT_ANSWERED = "expert_answered"
    CLOSED = "closed"


class CandidateOrigin(StrEnum):
    ANSWER_TIME = "answer_time"
    ENRICHMENT = "enrichment"


class CandidateStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class EventType(StrEnum):
    ANSWER_DELTA = "answer.delta"
    ANSWER_FINAL = "answer.final"
    STATUS_EXTERNAL_SEARCH = "status.external_search"
    STATUS_EXPERT_PENDING = "status.expert_pending"
    ANSWER_EXPERT = "answer.expert"
    ERROR = "error"
