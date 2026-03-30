import pytest
from app.learning.spaced_repetition import SRCard, calculate_next


def make_card(ef=2.5, interval=1, reps=0) -> SRCard:
    return SRCard(ease_factor=ef, interval_days=interval, repetitions=reps)


class TestRemembered:
    def test_interval_1_on_first_correct(self):
        result = calculate_next(make_card(reps=0), "remembered")
        assert result.interval_days == 1
        assert result.repetitions == 1

    def test_interval_6_on_second_correct(self):
        result = calculate_next(make_card(reps=1, interval=1), "remembered")
        assert result.interval_days == 6
        assert result.repetitions == 2

    def test_interval_multiplied_on_third_plus(self):
        result = calculate_next(make_card(ef=2.5, interval=6, reps=2), "remembered")
        assert result.interval_days == round(6 * 2.5)  # 15
        assert result.repetitions == 3

    def test_ease_factor_capped_at_2_5(self):
        result = calculate_next(make_card(ef=2.5), "remembered")
        assert result.ease_factor == 2.5

    def test_ease_factor_increases_when_below_max(self):
        result = calculate_next(make_card(ef=1.8), "remembered")
        assert abs(result.ease_factor - 1.9) < 0.001

    def test_next_review_at_in_future(self):
        from datetime import datetime
        result = calculate_next(make_card(), "remembered")
        assert result.next_review_at > datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)


class TestRepeat:
    def test_interval_resets_to_1(self):
        result = calculate_next(make_card(interval=15, reps=3), "repeat")
        assert result.interval_days == 1

    def test_repetitions_reset_to_0(self):
        result = calculate_next(make_card(reps=5), "repeat")
        assert result.repetitions == 0

    def test_ease_factor_decreases(self):
        result = calculate_next(make_card(ef=2.0), "repeat")
        assert abs(result.ease_factor - 1.8) < 0.001

    def test_ease_factor_clamped_at_minimum(self):
        result = calculate_next(make_card(ef=1.3), "repeat")
        assert result.ease_factor == 1.3


class TestScheduling:
    def test_schedules_1_day_ahead_for_remembered(self):
        from datetime import datetime, timedelta
        result = calculate_next(make_card(reps=0), "remembered")
        tomorrow = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        assert result.next_review_at.date() == tomorrow.date()

    def test_schedules_1_day_ahead_for_repeat(self):
        from datetime import datetime, timedelta
        result = calculate_next(make_card(reps=5, interval=15), "repeat")
        tomorrow = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        assert result.next_review_at.date() == tomorrow.date()
