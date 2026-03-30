from datetime import datetime
from pydantic import field_validator

from app.base_schema import CamelModel, Pagination
from app.languages.schemas import LanguageOut


class CreateSetRequest(CamelModel):
    name: str
    description: str | None = None
    language_id: int

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()


class UpdateSetRequest(CamelModel):
    name: str | None = None
    description: str | None = None


class CreateSetFromCardsRequest(CamelModel):
    name: str
    language_id: int
    description: str | None = None
    card_ids: list[int]

    @field_validator("name")
    @classmethod
    def name_not_empty_from_cards(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()

    @field_validator("card_ids")
    @classmethod
    def card_ids_not_empty(cls, v: list[int]) -> list[int]:
        if not v:
            raise ValueError("At least one card must be selected")
        return v


class FlashcardSetOut(CamelModel):
    id: int
    name: str
    description: str | None
    card_count: int        # → "cardCount"
    language: LanguageOut
    created_at: datetime   # → "createdAt"


class PaginatedSetsResponse(CamelModel):
    data: list[FlashcardSetOut]
    pagination: Pagination
