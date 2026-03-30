from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app import models
from app.flashcard_sets import service
from app.flashcard_sets.schemas import (
    CreateSetRequest,
    FlashcardSetOut,
    PaginatedSetsResponse,
    UpdateSetRequest,
)

router = APIRouter()


@router.get("", response_model=PaginatedSetsResponse)
def list_sets(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = service.find_all_by_user(db, current_user.id)
    return {
        "data": data,
        "pagination": {"page": 1, "page_size": len(data), "total": len(data)},
    }


@router.get("/{set_id}", response_model=FlashcardSetOut)
def get_set(
    set_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.find_one_or_fail(db, set_id, current_user.id)


@router.post("", response_model=FlashcardSetOut, status_code=status.HTTP_201_CREATED)
def create_set(
    body: CreateSetRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.create(db, current_user.id, body)


@router.patch("/{set_id}", response_model=FlashcardSetOut)
def update_set(
    set_id: int,
    body: UpdateSetRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.update(db, set_id, current_user.id, body)


@router.delete("/{set_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_set(
    set_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service.delete(db, set_id, current_user.id)
