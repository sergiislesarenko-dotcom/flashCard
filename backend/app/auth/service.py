from datetime import datetime, timedelta

from fastapi import HTTPException, Response, Request, status
import jwt
from jwt import PyJWTError as JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app import models

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=settings.bcrypt_rounds)

COOKIE_NAME = "refresh_token"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: int, email: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_expire_minutes)
    payload = {"sub": str(user_id), "email": email, "exp": expire}
    return jwt.encode(payload, settings.jwt_access_secret, algorithm="HS256")


def create_refresh_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(days=settings.jwt_refresh_expire_days)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.jwt_refresh_secret, algorithm="HS256")


def _store_refresh_token(db: Session, user_id: int, raw_token: str) -> None:
    hashed = pwd_context.hash(raw_token)
    expires_at = datetime.utcnow() + timedelta(days=settings.jwt_refresh_expire_days)
    db_token = models.RefreshToken(user_id=user_id, token_hash=hashed, expires_at=expires_at)
    db.add(db_token)
    db.commit()


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=False,  # True in production
        samesite="strict",
        max_age=settings.jwt_refresh_expire_days * 86400,
        path="/",
    )


def register(db: Session, email: str, password: str, display_name: str) -> models.User:
    existing = db.query(models.User).filter(models.User.email == email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = models.User(
        email=email,
        display_name=display_name,
        password_hash=hash_password(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login(db: Session, email: str, password: str, response: Response) -> dict:
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token(user.id, user.email)
    refresh_token = create_refresh_token(user.id)
    _store_refresh_token(db, user.id, refresh_token)
    _set_refresh_cookie(response, refresh_token)
    return {"access_token": access_token, "user": user}


def refresh(db: Session, request: Request, response: Response) -> dict:
    raw_token = request.cookies.get(COOKIE_NAME)
    if not raw_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")

    try:
        payload = jwt.decode(raw_token, settings.jwt_refresh_secret, algorithms=["HS256"], options={"verify_exp": True})
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    # Find a stored token that matches
    stored_tokens = db.query(models.RefreshToken).filter(
        models.RefreshToken.user_id == user_id,
        models.RefreshToken.expires_at > datetime.utcnow(),
    ).all()

    matched = None
    for stored in stored_tokens:
        if pwd_context.verify(raw_token, stored.token_hash):
            matched = stored
            break

    if not matched:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token not found or expired")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # Rotate: delete old, issue new
    db.delete(matched)
    db.commit()

    new_refresh = create_refresh_token(user.id)
    _store_refresh_token(db, user.id, new_refresh)
    _set_refresh_cookie(response, new_refresh)

    return {"access_token": create_access_token(user.id, user.email)}


def logout(db: Session, request: Request, response: Response) -> None:
    raw_token = request.cookies.get(COOKIE_NAME)
    if raw_token:
        try:
            payload = jwt.decode(raw_token, settings.jwt_refresh_secret, algorithms=["HS256"], options={"verify_exp": True})
            user_id = int(payload["sub"])
            stored_tokens = db.query(models.RefreshToken).filter(
                models.RefreshToken.user_id == user_id
            ).all()
            for stored in stored_tokens:
                if pwd_context.verify(raw_token, stored.token_hash):
                    db.delete(stored)
                    break
            db.commit()
        except Exception:
            pass
    response.delete_cookie(key=COOKIE_NAME, path="/")
