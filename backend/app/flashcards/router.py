from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app import models
from app.flashcards import service
from app.flashcards.schemas import (
    CreateCardRequest,
    FlashcardOut,
    ImportCardsRequest,
    PaginatedCardsResponse,
    UpdateCardRequest,
)

router = APIRouter()


@router.get("/all", response_model=PaginatedCardsResponse)
def list_all_cards(
    page: int = 1,
    page_size: int = 25,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cards, total = service.find_all_by_user(db, current_user.id, page, page_size)
    return {
        "data": cards,
        "pagination": {"page": page, "page_size": page_size, "total": total},
    }


@router.get("", response_model=list[FlashcardOut])
def list_cards(
    set_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.find_by_set(db, set_id, current_user.id)


@router.post("", response_model=FlashcardOut, status_code=status.HTTP_201_CREATED)
def create_card(
    body: CreateCardRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.create(db, current_user.id, body)


@router.post("/import", response_model=list[FlashcardOut], status_code=status.HTTP_201_CREATED)
def import_cards(
    body: ImportCardsRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.bulk_import(db, current_user.id, body)


@router.patch("/{card_id}", response_model=FlashcardOut)
def update_card(
    card_id: int,
    body: UpdateCardRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.update(db, card_id, current_user.id, body)


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(
    card_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service.delete(db, card_id, current_user.id)
