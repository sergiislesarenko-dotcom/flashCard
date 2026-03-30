from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models


def get_overview(db: Session, user_id: int) -> dict:
    total_sets = db.query(func.count(models.FlashcardSet.id)).filter(
        models.FlashcardSet.user_id == user_id
    ).scalar() or 0

    total_cards = (
        db.query(func.sum(models.FlashcardSet.card_count))
        .filter(models.FlashcardSet.user_id == user_id)
        .scalar()
        or 0
    )

    now = datetime.utcnow()
    # Count due cards across all sets owned by user
    due_today = (
        db.query(func.count(models.Flashcard.id))
        .join(models.FlashcardSet, models.Flashcard.set_id == models.FlashcardSet.id)
        .filter(
            models.FlashcardSet.user_id == user_id,
            models.Flashcard.next_review_at <= now,
        )
        .scalar()
        or 0
    )

    sessions_completed = db.query(func.count(models.LearningSession.id)).filter(
        models.LearningSession.user_id == user_id,
        models.LearningSession.status == models.SessionStatus.completed,
    ).scalar() or 0

    streak = _calculate_streak(db, user_id)

    # Average accuracy from completed sessions
    sessions = db.query(models.LearningSession).filter(
        models.LearningSession.user_id == user_id,
        models.LearningSession.status == models.SessionStatus.completed,
        models.LearningSession.cards_reviewed > 0,
    ).all()

    avg_accuracy = 0.0
    if sessions:
        total_accuracy = sum(
            s.cards_remembered / s.cards_reviewed * 100 for s in sessions
        )
        avg_accuracy = round(total_accuracy / len(sessions), 1)

    return {
        "total_sets": total_sets,
        "total_cards": int(total_cards),
        "due_today": due_today,
        "sessions_completed": sessions_completed,
        "streak_days": streak,
        "average_accuracy": avg_accuracy,
    }


def get_progress(db: Session, user_id: int, from_date: datetime, to_date: datetime) -> list[dict]:
    sessions = db.query(models.LearningSession).filter(
        models.LearningSession.user_id == user_id,
        models.LearningSession.status == models.SessionStatus.completed,
        models.LearningSession.completed_at >= from_date,
        models.LearningSession.completed_at <= to_date,
    ).all()

    by_date: dict[str, dict] = {}
    for s in sessions:
        if not s.completed_at:
            continue
        date_key = s.completed_at.strftime("%Y-%m-%d")
        if date_key not in by_date:
            by_date[date_key] = {"sessions_completed": 0, "cards_reviewed": 0, "cards_remembered": 0}
        by_date[date_key]["sessions_completed"] += 1
        by_date[date_key]["cards_reviewed"] += s.cards_reviewed
        by_date[date_key]["cards_remembered"] += s.cards_remembered

    return [{"date": k, **v} for k, v in sorted(by_date.items())]


def _calculate_streak(db: Session, user_id: int) -> int:
    today = datetime.utcnow().date()
    streak = 0
    check_date = today

    for _ in range(365):
        day_start = datetime.combine(check_date, datetime.min.time())
        day_end = datetime.combine(check_date, datetime.max.time())

        count = db.query(func.count(models.LearningSession.id)).filter(
            models.LearningSession.user_id == user_id,
            models.LearningSession.status == models.SessionStatus.completed,
            models.LearningSession.completed_at >= day_start,
            models.LearningSession.completed_at <= day_end,
        ).scalar() or 0

        if count > 0:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break

    return streak
