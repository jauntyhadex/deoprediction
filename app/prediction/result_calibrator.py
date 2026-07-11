class ResultCalibrator:

    DRAW_MINIMUM_PROBABILITY = 26.0
    DRAW_MAXIMUM_SIDE_GAP = 18.0
    DRAW_MAXIMUM_LEADER_GAP = 16.0

    @staticmethod
    def calibrate_result(
        home_probability: float,
        draw_probability: float,
        away_probability: float,
    ) -> str:

        strongest_side_probability = max(
            home_probability,
            away_probability,
        )

        side_gap = abs(
            home_probability - away_probability
        )

        leader_gap = (
            strongest_side_probability
            - draw_probability
        )

        draw_candidate = (
            draw_probability
            >= ResultCalibrator.DRAW_MINIMUM_PROBABILITY
            and side_gap
            <= ResultCalibrator.DRAW_MAXIMUM_SIDE_GAP
            and leader_gap
            <= ResultCalibrator.DRAW_MAXIMUM_LEADER_GAP
        )

        if draw_candidate:
            return "DRAW"

        if home_probability >= away_probability:
            return "HOME"

        return "AWAY"

    @staticmethod
    def calibrate_probabilities(
        home_probability: float,
        draw_probability: float,
        away_probability: float,
    ) -> dict:

        total = (
            home_probability
            + draw_probability
            + away_probability
        )

        if total <= 0:
            return {
                "home": 33.33,
                "draw": 33.34,
                "away": 33.33,
            }

        return {
            "home": round(
                home_probability / total * 100,
                2,
            ),
            "draw": round(
                draw_probability / total * 100,
                2,
            ),
            "away": round(
                away_probability / total * 100,
                2,
            ),
        }