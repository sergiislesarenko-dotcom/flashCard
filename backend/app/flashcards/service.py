from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import models
from app.flashcard_sets.service import find_one_or_fail as find_set_or_fail, increment_card_count
from app.flashcards.schemas import CreateCardRequest, UpdateCardRequest, ImportCardsRequest


def find_by_set(db: Session, set_id: int, user_id: int) -> list[models.Flashcard]:
    find_set_or_fail(db, set_id, user_id)  # ownership check
    return (
        db.query(models.Flashcard)
        .filter(models.Flashcard.set_id == set_id)
        .order_by(models.Flashcard.next_review_at.asc())
        .all()
    )


def find_one_or_fail(db: Session, card_id: int, user_id: int) -> models.Flashcard:
    card = db.query(models.Flashcard).filter(models.Flashcard.id == card_id).first()
    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
    # verify ownership via set
    from app.flashcard_sets.service import find_one_or_fail as set_find
    set_find(db, card.set_id, user_id)
    return card


def create(db: Session, user_id: int, dto: CreateCardRequest) -> models.Flashcard:
    from app.flashcard_sets.service import find_one_or_fail as set_find
    set_find(db, dto.set_id, user_id)  # ownership check
    card = models.Flashcard(
        set_id=dto.set_id,
        front=dto.front,
        back=dto.back,
        next_review_at=datetime.utcnow(),
    )
    db.add(card)
    db.flush()
    increment_card_count(db, dto.set_id, 1)
    db.commit()
    db.refresh(card)
    return card


def update(db: Session, card_id: int, user_id: int, dto: UpdateCardRequest) -> models.Flashcard:
    card = find_one_or_fail(db, card_id, user_id)
    if dto.front is not None:
        card.front = dto.front
    if dto.back is not None:
        card.back = dto.back
    db.commit()
    db.refresh(card)
    return card


def delete(db: Session, card_id: int, user_id: int) -> None:
    card = find_one_or_fail(db, card_id, user_id)
    set_id = card.set_id
    db.delete(card)
    db.flush()
    increment_card_count(db, set_id, -1)
    db.commit()


def bulk_import(db: Session, user_id: int, dto: ImportCardsRequest) -> list[models.Flashcard]:
    from app.flashcard_sets.service import find_one_or_fail as set_find
    set_find(db, dto.set_id, user_id)
    now = datetime.utcnow()
    cards = [
        models.Flashcard(
            set_id=dto.set_id,
            front=item.front,
            back=item.back,
            next_review_at=now,
        )
        for item in dto.cards
    ]
    db.add_all(cards)
    db.flush()
    increment_card_count(db, dto.set_id, len(cards))
    db.commit()
    for c in cards:
        db.refresh(c)
    return cards


def find_due_cards(db: Session, set_id: int, limit: int) -> list[models.Flashcard]:
    now = datetime.utcnow()
    return (
        db.query(models.Flashcard)
        .filter(
            models.Flashcard.set_id == set_id,
            models.Flashcard.next_review_at <= now,
        )
        .order_by(models.Flashcard.next_review_at.asc())
        .limit(limit)
        .all()
    )


def find_oldest_cards(db: Session, set_id: int, limit: int) -> list[models.Flashcard]:
    return (
        db.query(models.Flashcard)
        .filter(models.Flashcard.set_id == set_id)
        .order_by(models.Flashcard.next_review_at.asc())
        .limit(limit)
        .all()
    )
