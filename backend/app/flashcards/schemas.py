from datetime import datetime
from decimal import Decimal
from pydantic import field_validator

from app.base_schema import CamelModel


class CreateCardRequest(CamelModel):
    set_id: int
    front: str
    back: str

    @field_validator("front", "back")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field cannot be empty")
        if len(v) > 500:
            raise ValueError("Field cannot exceed 500 characters")
        return v.strip()


class UpdateCardRequest(CamelModel):
    front: str | None = None
    back: str | None = None


class CardImportItem(CamelModel):
    front: str
    back: str


class ImportCardsRequest(CamelModel):
    set_id: int
    cards: list[CardImportItem]


class FlashcardOut(CamelModel):
    id: int
    set_id: int           # → "setId"
    front: str
    back: str
    ease_factor: Decimal  # → "easeFactor"
    interval_days: int    # → "intervalDays"
    repetitions: int
    next_review_at: datetime | None  # → "nextReviewAt"
    created_at: datetime             # → "createdAt"
