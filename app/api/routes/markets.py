from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.services.market_catalog_service import (
    MarketCatalogService,
)


router = APIRouter(
    prefix="/markets",
    tags=["Market Catalog"],
)


def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


@router.get("/catalog")
def get_market_catalog(
    db: Session = Depends(get_db),
):

    service = MarketCatalogService(db)

    catalog = service.get_catalog()

    return {
        "count": len(
            catalog["market_types"]
        ),
        **catalog,
    }


@router.get("/types")
def get_market_types(
    db: Session = Depends(get_db),
):

    market_types = (
        MarketCatalogService(db)
        .get_market_types()
    )

    return {
        "count": len(market_types),
        "market_types": market_types,
    }


@router.get("/types/{market_type}")
def get_market_type(
    market_type: str,
    db: Session = Depends(get_db),
):

    normalized_market_type = (
        market_type.strip().upper()
    )

    market_types = (
        MarketCatalogService(db)
        .get_market_types()
    )

    for item in market_types:

        if (
            item["market_type"]
            == normalized_market_type
        ):

            return {
                "market_type": item
            }

    raise HTTPException(
        status_code=404,
        detail=(
            "Market type not found."
        ),
    )


@router.get("/selections")
def get_market_selections(
    db: Session = Depends(get_db),
):

    selections = (
        MarketCatalogService(db)
        .get_selections()
    )

    return {
        "count": len(selections),
        "selections": selections,
    }


@router.get("/grades")
def get_pick_grades(
    db: Session = Depends(get_db),
):

    grades = (
        MarketCatalogService(db)
        .get_pick_grades()
    )

    return {
        "count": len(grades),
        "grades": grades,
    }
