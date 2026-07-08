from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import model_loader
from app.database.connection import SessionLocal
from app.services.prediction_pick_service import (
    PredictionPickService,
)


router = APIRouter(
    prefix="/prediction-picks",
    tags=["Prediction Picks"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.get("/top")
def get_top_prediction_picks(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    minimum_grade: str | None = Query(
        default=None,
    ),
    db: Session = Depends(get_db),
):
    service = PredictionPickService(db)

    picks = service.get_top_picks(
        limit=limit,
        minimum_grade=minimum_grade,
    )

    return {
        "count": len(picks),
        "picks": picks,
    }


@router.get("/fixture/{fixture_id}")
def get_fixture_prediction_picks(
    fixture_id: int,
    limit: int = Query(
        default=5,
        ge=1,
        le=20,
    ),
    db: Session = Depends(get_db),
):
    service = PredictionPickService(db)

    picks = service.get_fixture_picks(
        fixture_id=fixture_id,
        limit=limit,
    )

    if not picks:
        raise HTTPException(
            status_code=404,
            detail="Prediction picks not found.",
        )

    return {
        "fixture_id": fixture_id,
        "count": len(picks),
        "picks": picks,
    }