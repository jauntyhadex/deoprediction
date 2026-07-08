from collections import defaultdict

from app.prediction.confidence import ConfidenceCalculator


class MarketRanker:

    THREE_WAY_MARKETS = {
        "MATCH_RESULT",
        "FIRST_HALF_RESULT",
        "SECOND_HALF_RESULT",
    }

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

        if market_type == "CORRECT_SCORE":
            return 8.0

        return 55.0

    @staticmethod
    def calculate_score(market) -> float:

        return round(
            float(market.confidence) * 0.70
            + float(market.probability) * 0.30,
            2,
        )

    @staticmethod
    def rank(
        markets,
        limit: int = 5,
    ) -> list:

        grouped = defaultdict(list)

        for market in markets:
            grouped[
                MarketRanker.group_key(market)
            ].append(market)

        best_per_group = []

        for group in grouped.values():

            best_market = max(
                group,
                key=lambda market: (
                    float(market.probability),
                    float(market.confidence),
                ),
            )

            best_per_group.append(
                {
                    "market": best_market,
                    "score": MarketRanker.calculate_score(
                        best_market
                    ),
                    "grade": ConfidenceCalculator.grade(
                        best_market.confidence
                    ),
                }
            )

        strict_candidates = []
        fallback_candidates = []

        for item in best_per_group:

            market = item["market"]

            minimum = MarketRanker.minimum_probability(
                market.market_type
            )

            is_strict = (
                1.15 <= market.fair_odds <= 12
                and market.probability >= minimum
            )

            if is_strict:
                strict_candidates.append(item)
            else:
                fallback_candidates.append(item)

        strict_candidates.sort(
            key=lambda item: (
                item["score"],
                item["market"].probability,
            ),
            reverse=True,
        )

        fallback_candidates.sort(
            key=lambda item: (
                item["score"],
                item["market"].probability,
            ),
            reverse=True,
        )

        ranked = strict_candidates[:limit]

        used_market_ids = {
            item["market"].id
            for item in ranked
        }

        for item in fallback_candidates:

            if len(ranked) >= limit:
                break

            if item["market"].id in used_market_ids:
                continue

            ranked.append(item)
            used_market_ids.add(
                item["market"].id
            )

        return ranked