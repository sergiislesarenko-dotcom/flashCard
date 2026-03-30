from sqlalchemy.orm import Session
from app import models


def get_all(db: Session) -> list[models.Language]:
    return db.query(models.Language).order_by(models.Language.name).all()
