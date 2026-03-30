from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import service
from app.auth.schemas import LoginRequest, RegisterRequest, TokenResponse, RefreshTokenResponse, UserResponse

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    user = service.register(db, body.email, body.password, body.display_name)
    return user


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, response: Response, db: Session = Depends(get_db)):
    return service.login(db, body.email, body.password, response)


@router.post("/refresh", response_model=RefreshTokenResponse)
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    return service.refresh(db, request, response)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    service.logout(db, request, response)
