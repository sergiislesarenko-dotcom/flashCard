from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt import PyJWTError as JWTError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app import models

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_access_secret, algorithms=["HS256"], options={"verify_exp": True})
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise exc

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise exc
    return user
