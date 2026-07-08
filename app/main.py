from fastapi import FastAPI

from app.database import model_loader
from app.api.routes.prediction_picks import (
    router as prediction_picks_router,
)


app = FastAPI(
    title="DeoPrediction API",
    description="Football and basketball prediction API",
    version="1.0.0",
)


app.include_router(prediction_picks_router)


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