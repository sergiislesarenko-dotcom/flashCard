from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app import models
from app.flashcard_sets.schemas import CreateSetRequest, UpdateSetRequest


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


def increment_card_count(db: Session, set_id: int, delta: int) -> None:
    fset = db.query(models.FlashcardSet).filter(models.FlashcardSet.id == set_id).first()
    if fset:
        fset.card_count = fset.card_count + delta
        db.commit()
