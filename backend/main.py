from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.auth.router import router as auth_router
from app.languages.router import router as languages_router
from app.flashcard_sets.router import router as sets_router
from app.flashcards.router import router as cards_router
from app.learning.router import router as learning_router
from app.stats.router import router as stats_router

app = FastAPI(title="FlashLang API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(languages_router, prefix="/languages", tags=["languages"])
app.include_router(sets_router, prefix="/sets", tags=["sets"])
app.include_router(cards_router, prefix="/cards", tags=["cards"])
app.include_router(learning_router, prefix="/learning", tags=["learning"])
app.include_router(stats_router, prefix="/stats", tags=["stats"])
