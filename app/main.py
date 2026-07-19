from fastapi import FastAPI
from app.config.settings import settings
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.discovery import (
    router as discovery_router,
)

from app.api.routes.markets import (
    router as markets_router,
)

from app.api.routes.teams import (
    router as teams_router,
)

from app.api.routes.fixtures import (
    router as fixtures_router,
)

from app.api.routes.competitions import (
    router as competitions_router,
)

from app.api.routes.auth import (
    router as auth_router,
)

from app.database import model_loader
from app.api.routes.prediction_picks import (
    router as prediction_picks_router,
)
from app.api.routes.system_status import (
    router as system_status_router,
)
from app.api.routes.timezones import (
    router as timezones_router,
)



def get_cors_allowed_origins() -> list[str]:

    raw_origins = (
        settings.cors_allowed_origins
        or "*"
    ).strip()

    if raw_origins == "*":
        return ["*"]

    return [
        origin.strip()
        for origin in raw_origins.split(",")
        if origin.strip()
    ]


app = FastAPI(
    title="DeoPrediction API",
    description="Football and basketball prediction API",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_allowed_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    prediction_picks_router
)

app.include_router(
    system_status_router
)

app.include_router(
    timezones_router
)

app.include_router(
    competitions_router
)

app.include_router(
    fixtures_router
)

app.include_router(
    teams_router
)

app.include_router(
    markets_router
)

app.include_router(
    discovery_router
)

app.include_router(
    auth_router
)


@app.get("/")
def root():
    return {
        "message": "DeoPrediction API is running",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }
