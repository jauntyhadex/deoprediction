from app.models.prediction_market import PredictionMarket
from app.prediction.confidence import ConfidenceCalculator


class PredictionMarketService:

    def __init__(self, db):
        self.db = db

    @staticmethod
    def fair_odds(probability: float) -> float:

        if probability <= 0:
            return 0.0

        return round(
            100 / probability,
            2,
        )

    def create(self, **kwargs):

        probability = float(
            kwargs["probability"]
        )

        market_type = kwargs["market_type"]

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