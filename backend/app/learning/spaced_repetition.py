"""Pure SM-2 spaced repetition algorithm — no DB dependency."""
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal


@dataclass
class SRCard:
    ease_factor: float
    interval_days: int
    repetitions: int


@dataclass
class SRResult:
    ease_factor: float
    interval_days: int
    repetitions: int
    next_review_at: datetime


def calculate_next(card: SRCard, result: str) -> SRResult:
    """
    result: "remembered" | "repeat"
    """
    ef = float(card.ease_factor)
    interval = card.interval_days
    reps = card.repetitions

    if result == "remembered":
        if reps == 0:
            interval = 1
        elif reps == 1:
            interval = 6
        else:
            interval = round(interval * ef)
        ef = min(2.5, ef + 0.1)
        reps += 1
    else:  # repeat
        interval = 1
        ef = max(1.3, ef - 0.2)
        reps = 0

    # Schedule at midnight of the target day
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    next_review_at = today + timedelta(days=interval)

    return SRResult(
        ease_factor=round(ef, 2),
        interval_days=interval,
        repetitions=reps,
        next_review_at=next_review_at,
    )
