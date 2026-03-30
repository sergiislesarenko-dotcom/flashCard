from app.base_schema import CamelModel


class StatsOverview(CamelModel):
    total_sets: int
    total_cards: int
    due_today: int
    sessions_completed: int
    streak_days: int
    average_accuracy: float


class DailyProgress(CamelModel):
    date: str
    sessions_completed: int
    cards_reviewed: int
    cards_remembered: int
