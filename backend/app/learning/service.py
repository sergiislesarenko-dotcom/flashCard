from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import models
from app.flashcard_sets.service import find_one_or_fail as find_set
from app.flashcards.service import find_due_cards, find_oldest_cards
from app.learning.schemas import CreateSessionRequest, SubmitReviewRequest
from app.learning.spaced_repetition import SRCard, calculate_next


def create_session(db: Session, user_id: int, dto: CreateSessionRequest) -> dict:
    flashcard_set = find_set(db, dto.set_id, user_id)  # ownership check

    if dto.card_count is None:
        # All cards in the set: due first, then the rest
        cards = (
            db.query(models.Flashcard)
            .filter(models.Flashcard.set_id == dto.set_id)
            .order_by(models.Flashcard.next_review_at.asc())
            .all()
        )
    else:
        due_cards = find_due_cards(db, dto.set_id, dto.card_count)
        if len(due_cards) < dto.card_count:
            remaining = dto.card_count - len(due_cards)
            due_ids = {c.id for c in due_cards}
            oldest = find_oldest_cards(db, dto.set_id, dto.card_count)
            filler = [c for c in oldest if c.id not in due_ids][:remaining]
            cards = due_cards + filler
        else:
            cards = due_cards

    session = models.LearningSession(
        user_id=user_id,
        set_id=dto.set_id,
        total_cards=len(cards),
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return {
        "session_id": session.id,
        "set_id": session.set_id,
        "language_code": flashcard_set.language.code,
        "cards": [{"id": c.id, "front": c.front, "back": c.back} for c in cards],
        "total_cards": len(cards),
        "started_at": session.started_at,
    }


def get_session(db: Session, session_id: int, user_id: int) -> dict:
    session = _get_session_or_fail(db, session_id, user_id)
    return {
        "session_id": session.id,
        "set_id": session.set_id,
        "status": session.status.value if hasattr(session.status, "value") else session.status,
        "total_cards": session.total_cards,
        "cards_reviewed": session.cards_reviewed,
        "cards_remembered": session.cards_remembered,
        "started_at": session.started_at,
        "completed_at": session.completed_at,
    }


def submit_review(db: Session, session_id: int, user_id: int, dto: SubmitReviewRequest) -> dict:
    session = _get_session_or_fail(db, session_id, user_id)
    status_val = session.status.value if hasattr(session.status, "value") else session.status
    if status_val != "active":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Session is no longer active")

    already = db.query(models.ReviewResult).filter(
        models.ReviewResult.session_id == session_id,
        models.ReviewResult.card_id == dto.card_id,
    ).first()
    if already:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Card already reviewed in this session")

    card = db.query(models.Flashcard).filter(models.Flashcard.id == dto.card_id).first()
    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
    if card.set_id != session.set_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Card does not belong to session's set")

    sr_input = SRCard(
        ease_factor=float(card.ease_factor),
        interval_days=card.interval_days,
        repetitions=card.repetitions,
    )
    sr = calculate_next(sr_input, dto.result)

    card.ease_factor = sr.ease_factor
    card.interval_days = sr.interval_days
    card.repetitions = sr.repetitions
    card.next_review_at = sr.next_review_at

    review = models.ReviewResult(
        session_id=session_id,
        card_id=dto.card_id,
        result=models.ReviewOutcome(dto.result),
        ease_factor=sr.ease_factor,
        interval_days=sr.interval_days,
        next_review_at=sr.next_review_at,
    )
    db.add(review)

    session.cards_reviewed = session.cards_reviewed + 1
    if dto.result == "remembered":
        session.cards_remembered = session.cards_remembered + 1

    db.commit()

    return {
        "card_id": dto.card_id,
        "result": dto.result,
        "next_review_at": sr.next_review_at,
        "interval_days": sr.interval_days,
        "ease_factor": sr.ease_factor,
        "repetitions": sr.repetitions,
    }


def complete_session(db: Session, session_id: int, user_id: int) -> dict:
    session = _get_session_or_fail(db, session_id, user_id)
    completed_at = datetime.utcnow()
    session.status = models.SessionStatus.completed
    session.completed_at = completed_at
    db.commit()

    repeat_count = session.cards_reviewed - session.cards_remembered
    accuracy = (
        round((session.cards_remembered / session.cards_reviewed) * 100)
        if session.cards_reviewed > 0
        else 0
    )

    return {
        "session_id": session.id,
        "status": "completed",
        "total_cards": session.total_cards,
        "cards_reviewed": session.cards_reviewed,
        "cards_remembered": session.cards_remembered,
        "repeat_count": repeat_count,
        "accuracy_percent": accuracy,
        "completed_at": completed_at,
    }


def _get_session_or_fail(db: Session, session_id: int, user_id: int) -> models.LearningSession:
    session = db.query(models.LearningSession).filter(models.LearningSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return session
