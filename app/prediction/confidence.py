class ConfidenceCalculator:

    THREE_WAY_MARKETS = {
        "MATCH_RESULT",
        "FIRST_HALF_RESULT",
        "SECOND_HALF_RESULT",
    }

    BINARY_MARKETS = {
        "BTTS",
        "DOUBLE_CHANCE",
        "DRAW_NO_BET",
        "TOTAL_GOALS",
        "HOME_TEAM_TOTAL",
        "AWAY_TEAM_TOTAL",
        "CLEAN_SHEET",
        "WIN_TO_NIL",
        "ASIAN_HANDICAP",
        "FIRST_HALF_BTTS",
        "SECOND_HALF_BTTS",
        "FIRST_HALF_TOTAL_GOALS",
        "SECOND_HALF_TOTAL_GOALS",
    }

    @staticmethod
    def calculate(
        market_type: str,
        probability: float,
    ) -> float:

        probability = max(
            0.0,
            min(float(probability), 100.0),
        )

        if market_type in ConfidenceCalculator.THREE_WAY_MARKETS:
            baseline = 100 / 3

            confidence = (
                (probability - baseline)
                / (100 - baseline)
            ) * 100

        elif market_type in ConfidenceCalculator.BINARY_MARKETS:
            confidence = (
                probability - 50
            ) * 2

        elif market_type == "CORRECT_SCORE":
            confidence = probability * 3

        else:
            confidence = probability

        return round(
            max(0.0, min(confidence, 100.0)),
            2,
        )

    @staticmethod
    def grade(confidence: float) -> str:

        if confidence >= 80:
            return "A+"

        if confidence >= 70:
            return "A"

        if confidence >= 60:
            return "B"

        if confidence >= 45:
            return "C"

        if confidence >= 30:
            return "D"

        return "E"