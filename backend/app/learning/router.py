from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app import models
from app.learning import service
from app.learning.schemas import (
    CreateSessionRequest,
    ReviewResultOut,
    SessionOut,
    SessionStartResponse,
    SessionSummary,
    SubmitReviewRequest,
)

router = APIRouter()


@router.post("/sessions", response_model=SessionStartResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    body: CreateSessionRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.create_session(db, current_user.id, body)


@router.get("/sessions/{session_id}", response_model=SessionOut)
def get_session(
    session_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.get_session(db, session_id, current_user.id)


@router.post("/sessions/{session_id}/reviews", response_model=ReviewResultOut)
def submit_review(
    session_id: int,
    body: SubmitReviewRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.submit_review(db, session_id, current_user.id, body)


@router.post("/sessions/{session_id}/complete", response_model=SessionSummary)
def complete_session(
    session_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.complete_session(db, session_id, current_user.id)
