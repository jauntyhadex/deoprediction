from fastapi import FastAPI

from app.config.settings import settings
from app.database.connection import engine
from app.database.base import Base
from app.models import Competition, Player, Team

# Create all database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-assisted sports analysis platform.",
)


@app.get("/")
def home() -> dict[str, str]:
    return {
        "message": f"Welcome to {settings.app_name}!",
        "environment": settings.environment,
        "status": "running",
    }