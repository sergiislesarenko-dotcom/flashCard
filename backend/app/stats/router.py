from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app import models
from app.stats import service
from app.stats.schemas import DailyProgress, StatsOverview

router = APIRouter()


@router.get("/overview", response_model=StatsOverview)
def overview(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.get_overview(db, current_user.id)


@router.get("/progress", response_model=list[DailyProgress])
def progress(
    from_date: datetime = Query(default=None),
    to_date: datetime = Query(default=None),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if from_date is None:
        from_date = datetime.utcnow() - timedelta(days=30)
    if to_date is None:
        to_date = datetime.utcnow()
    return service.get_progress(db, current_user.id, from_date, to_date)
