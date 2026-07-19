from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.prediction_market import PredictionMarket
from app.models.prediction_pick import PredictionPick


class MarketCatalogService:

    def __init__(
        self,
        db: Session,
    ) -> None:

        self.db = db

    @staticmethod
    def display_name(
        value: str,
    ) -> str:

        return (
            value.replace("_", " ")
            .title()
        )

    def get_market_types(
        self,
    ) -> list[dict]:

        rows = (
            self.db.query(
                PredictionMarket.market_type,
                func.count(
                    PredictionMarket.id
                ).label("market_count"),
                func.min(
                    PredictionMarket.probability
                ).label("minimum_probability"),
                func.max(
                    PredictionMarket.probability
                ).label("maximum_probability"),
                func.min(
                    PredictionMarket.fair_odds
                ).label("minimum_fair_odds"),
                func.max(
                    PredictionMarket.fair_odds
                ).label("maximum_fair_odds"),
                func.min(
                    PredictionMarket.confidence
                ).label("minimum_confidence"),
                func.max(
                    PredictionMarket.confidence
                ).label("maximum_confidence"),
            )
            .group_by(
                PredictionMarket.market_type
            )
            .order_by(
                PredictionMarket.market_type.asc()
            )
            .all()
        )

        return [
            {
                "market_type": row.market_type,
                "display_name": (
                    self.display_name(
                        row.market_type
                    )
                ),
                "market_count": row.market_count,
                "probability_range": {
                    "minimum": (
                        row.minimum_probability
                    ),
                    "maximum": (
                        row.maximum_probability
                    ),
                },
                "fair_odds_range": {
                    "minimum": (
                        row.minimum_fair_odds
                    ),
                    "maximum": (
                        row.maximum_fair_odds
                    ),
                },
                "confidence_range": {
                    "minimum": (
                        row.minimum_confidence
                    ),
                    "maximum": (
                        row.maximum_confidence
                    ),
                },
                "selections": (
                    self.get_selections(
                        market_type=row.market_type
                    )
                ),
            }
            for row in rows
        ]

    def get_selections(
        self,
        market_type: str | None = None,
    ) -> list[dict]:

        query = self.db.query(
            PredictionMarket.selection,
            func.count(
                PredictionMarket.id
            ).label("market_count"),
        )

        if market_type is not None:

            query = query.filter(
                PredictionMarket.market_type
                == market_type.upper()
            )

        rows = (
            query.group_by(
                PredictionMarket.selection
            )
            .order_by(
                PredictionMarket.selection.asc()
            )
            .all()
        )

        return [
            {
                "selection": row.selection,
                "display_name": (
                    self.display_name(
                        row.selection
                    )
                ),
                "market_count": (
                    row.market_count
                ),
            }
            for row in rows
        ]

    def get_pick_grades(
        self,
    ) -> list[dict]:

        rows = (
            self.db.query(
                PredictionPick.grade,
                func.count(
                    PredictionPick.id
                ).label("pick_count"),
            )
            .group_by(
                PredictionPick.grade
            )
            .order_by(
                PredictionPick.grade.asc()
            )
            .all()
        )

        return [
            {
                "grade": row.grade,
                "display_name": row.grade,
                "pick_count": row.pick_count,
            }
            for row in rows
        ]

    def get_catalog(
        self,
    ) -> dict:

        return {
            "market_types": (
                self.get_market_types()
            ),
            "selections": (
                self.get_selections()
            ),
            "pick_grades": (
                self.get_pick_grades()
            ),
            "recommended_filters": {
                "minimum_fair_odds": 1.15,
                "maximum_fair_odds": 8.0,
                "minimum_probability": 0.0,
                "minimum_market_confidence": 0.0,
                "one_per_fixture": True,
                "upcoming_only": True,
                "days_ahead": 30,
            },
        }
