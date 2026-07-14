from fastapi import FastAPI

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


app = FastAPI(
    title="DeoPrediction API",
    description="Football and basketball prediction API",
    version="1.0.0",
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
