from collections import defaultdict

from app.prediction.confidence import (
    ConfidenceCalculator,
)


class MarketRanker:

    THREE_WAY_MARKETS = {
        "MATCH_RESULT",
        "FIRST_HALF_RESULT",
        "SECOND_HALF_RESULT",
    }

    EXCLUDED_MARKETS = {
        "CORRECT_SCORE",
    }

    MINIMUM_FAIR_ODDS = 1.15
    MAXIMUM_FAIR_ODDS = 8.00
    MAXIMUM_PROBABILITY = 86.95

    @staticmethod
    def group_key(market):

        line = market.line

        if market.market_type == "ASIAN_HANDICAP":
            line = abs(line or 0)

        return (
            market.market_type,
            line,
        )

    @staticmethod
    def minimum_probability(
        market_type: str,
    ) -> float:

        if market_type in MarketRanker.THREE_WAY_MARKETS:
            return 40.0

        return 55.0

    @staticmethod
    def calculate_score(market) -> float:

        probability = float(
            market.probability
        )

        confidence = float(
            market.confidence
        )

        score = (
            confidence * 0.70
            + probability * 0.30
        )

        return round(
            max(0.0, min(score, 100.0)),
            2,
        )

    @staticmethod
    def is_valid_market(market) -> bool:

        probability = float(
            market.probability
        )

        fair_odds = float(
            market.fair_odds
        )

        if (
            market.market_type
            in MarketRanker.EXCLUDED_MARKETS
        ):
            return False

        if probability <= 0:
            return False

        if (
            probability
            > MarketRanker.MAXIMUM_PROBABILITY
        ):
            return False

        if (
            fair_odds
            < MarketRanker.MINIMUM_FAIR_ODDS
        ):
            return False

        if (
            fair_odds
            > MarketRanker.MAXIMUM_FAIR_ODDS
        ):
            return False

        minimum_probability = (
            MarketRanker.minimum_probability(
                market.market_type
            )
        )

        if probability < minimum_probability:
            return False

        return True

    @staticmethod
    def rank(
        markets,
        limit: int = 5,
    ) -> list:

        grouped_markets = defaultdict(list)

        for market in markets:

            if not MarketRanker.is_valid_market(
                market
            ):
                continue

            grouped_markets[
                MarketRanker.group_key(market)
            ].append(market)

        candidates = []

        for group in grouped_markets.values():

            best_market = max(
                group,
                key=lambda market: (
                    float(market.probability),
                    float(market.confidence),
                ),
            )

            candidates.append(
                {
                    "market": best_market,
                    "score": (
                        MarketRanker.calculate_score(
                            best_market
                        )
                    ),
                    "grade": (
                        ConfidenceCalculator.grade(
                            best_market.confidence
                        )
                    ),
                }
            )

        candidates.sort(
            key=lambda item: (
                item["score"],
                item["market"].probability,
            ),
            reverse=True,
        )

        return candidates[:limit]