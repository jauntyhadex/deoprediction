from app.models.prediction_market import PredictionMarket


class PredictionMarketService:

    def __init__(self, db):
        self.db = db

    @staticmethod
    def fair_odds(probability: float):

        if probability <= 0:
            return 0

        return round(100 / probability, 2)

    def create(self, **kwargs):

        market = PredictionMarket(**kwargs)

        self.db.add(market)

        return market