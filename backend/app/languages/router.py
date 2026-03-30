from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.languages import service
from app.languages.schemas import LanguageOut

router = APIRouter()


@router.get("", response_model=list[LanguageOut])
def list_languages(db: Session = Depends(get_db)):
    return service.get_all(db)
