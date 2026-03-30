from datetime import datetime
from decimal import Decimal
from pydantic import field_validator

from app.base_schema import CamelModel


class CreateSessionRequest(CamelModel):
    set_id: int
    card_count: int = 20

    @field_validator("card_count")
    @classmethod
    def validate_count(cls, v: int) -> int:
        if v < 1 or v > 100:
            raise ValueError("card_count must be between 1 and 100")
        return v


class SessionCardOut(CamelModel):
    id: int
    front: str
    back: str


class SessionStartResponse(CamelModel):
    session_id: int    # → "sessionId"
    set_id: int        # → "setId"
    cards: list[SessionCardOut]
    total_cards: int   # → "totalCards"
    started_at: datetime  # → "startedAt"


class SessionOut(CamelModel):
    session_id: int
    set_id: int
    status: str
    total_cards: int
    cards_reviewed: int
    cards_remembered: int
    started_at: datetime
    completed_at: datetime | None


class SubmitReviewRequest(CamelModel):
    card_id: int
    result: str

    @field_validator("result")
    @classmethod
    def validate_result(cls, v: str) -> str:
        if v not in ("remembered", "repeat"):
            raise ValueError("result must be 'remembered' or 'repeat'")
        return v


class ReviewResultOut(CamelModel):
    card_id: int         # → "cardId"
    result: str
    next_review_at: datetime  # → "nextReviewAt"
    interval_days: int        # → "intervalDays"
    ease_factor: Decimal      # → "easeFactor"
    repetitions: int


class SessionSummary(CamelModel):
    session_id: int         # → "sessionId"
    status: str
    total_cards: int        # → "totalCards"
    cards_reviewed: int     # → "cardsReviewed"
    cards_remembered: int   # → "cardsRemembered"
    repeat_count: int       # → "repeatCount"
    accuracy_percent: int   # → "accuracyPercent"
    completed_at: datetime | None  # → "completedAt"
