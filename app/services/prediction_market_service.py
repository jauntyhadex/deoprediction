from app.models.prediction_market import PredictionMarket
from app.prediction.confidence import (
    ConfidenceCalculator,
)


class PredictionMarketService:

    def __init__(self, db):
        self.db = db

    @staticmethod
    def normalize_probability(
        probability: float,
    ) -> float:
        return round(
            max(
                0.0,
                min(float(probability), 100.0),
            ),
            2,
        )

    @staticmethod
    def fair_odds(
        probability: float,
    ) -> float:

        probability = (
            PredictionMarketService
            .normalize_probability(
                probability
            )
        )

        if probability <= 0:
            return 0.0

        return round(
            100 / probability,
            2,
        )

    def create(self, **kwargs):

        probability = self.normalize_probability(
            kwargs["probability"]
        )

        market_type = kwargs["market_type"]

        kwargs["probability"] = probability

        kwargs["fair_odds"] = self.fair_odds(
            probability
        )

        kwargs["confidence"] = (
            ConfidenceCalculator.calculate(
                market_type,
                probability,
            )
        )

        market = PredictionMarket(**kwargs)

        self.db.add(market)

        return market