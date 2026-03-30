from datetime import datetime

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app import models
from app.flashcard_sets.schemas import CreateSetRequest, CreateSetFromCardsRequest, UpdateSetRequest


def find_all_by_user(db: Session, user_id: int) -> list[models.FlashcardSet]:
    return (
        db.query(models.FlashcardSet)
        .filter(models.FlashcardSet.user_id == user_id)
        .order_by(models.FlashcardSet.created_at.desc())
        .all()
    )


def find_one_or_fail(db: Session, set_id: int, user_id: int) -> models.FlashcardSet:
    fset = db.query(models.FlashcardSet).filter(models.FlashcardSet.id == set_id).first()
    if not fset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Set not found")
    if fset.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return fset


def create(db: Session, user_id: int, dto: CreateSetRequest) -> models.FlashcardSet:
    language = db.query(models.Language).filter(models.Language.id == dto.language_id).first()
    if not language:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Language not found")
    fset = models.FlashcardSet(
        user_id=user_id,
        language_id=dto.language_id,
        name=dto.name,
        description=dto.description,
    )
    db.add(fset)
    db.commit()
    db.refresh(fset)
    return fset


def update(db: Session, set_id: int, user_id: int, dto: UpdateSetRequest) -> models.FlashcardSet:
    fset = find_one_or_fail(db, set_id, user_id)
    if dto.name is not None:
        fset.name = dto.name
    if dto.description is not None:
        fset.description = dto.description
    db.commit()
    db.refresh(fset)
    return fset


def delete(db: Session, set_id: int, user_id: int) -> None:
    fset = find_one_or_fail(db, set_id, user_id)
    db.delete(fset)
    db.commit()


def create_from_cards(db: Session, user_id: int, dto: CreateSetFromCardsRequest) -> models.FlashcardSet:
    language = db.query(models.Language).filter(models.Language.id == dto.language_id).first()
    if not language:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Language not found")

    # Verify all cards belong to the user
    cards = (
        db.query(models.Flashcard)
        .join(models.FlashcardSet, models.Flashcard.set_id == models.FlashcardSet.id)
        .filter(
            models.Flashcard.id.in_(dto.card_ids),
            models.FlashcardSet.user_id == user_id,
        )
        .all()
    )
    if len(cards) != len(dto.card_ids):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Some cards not found or not owned by you")

    fset = models.FlashcardSet(
        user_id=user_id,
        language_id=dto.language_id,
        name=dto.name,
        description=dto.description,
    )
    db.add(fset)
    db.flush()

    now = datetime.utcnow()
    new_cards = [
        models.Flashcard(
            set_id=fset.id,
            front=c.front,
            back=c.back,
            next_review_at=now,
        )
        for c in cards
    ]
    db.add_all(new_cards)
    fset.card_count = len(new_cards)
    db.commit()
    db.refresh(fset)
    return fset


def increment_card_count(db: Session, set_id: int, delta: int) -> None:
    fset = db.query(models.FlashcardSet).filter(models.FlashcardSet.id == set_id).first()
    if fset:
        fset.card_count = fset.card_count + delta
        db.commit()
