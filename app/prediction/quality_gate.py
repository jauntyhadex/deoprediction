from sqlalchemy import and_, or_


class PredictionQualityGate:

    MINIMUM_CONFIDENCE = 40.0
    MINIMUM_MARGIN = 5.0

    RESULT_FIELDS = {
        "HOME": "home_win_probability",
        "DRAW": "draw_probability",
        "AWAY": "away_win_probability",
    }

    @classmethod
    def details(
        cls,
        prediction,
    ) -> dict:

        if prediction is None:
            return {
                "predicted_result": None,
                "confidence": 0.0,
                "margin": 0.0,
                "passes": False,
            }

        probabilities = {
            result: float(
                getattr(
                    prediction,
                    field_name,
                    0.0,
                )
                or 0.0
            )
            for result, field_name
            in cls.RESULT_FIELDS.items()
        }

        ordered_probabilities = sorted(
            probabilities.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        predicted_result = (
            ordered_probabilities[0][0]
        )

        confidence = float(
            ordered_probabilities[0][1]
        )

        second_probability = float(
            ordered_probabilities[1][1]
        )

        margin = (
            confidence
            - second_probability
        )

        passes = (
            confidence
            >= cls.MINIMUM_CONFIDENCE
            and margin
            >= cls.MINIMUM_MARGIN
        )

        return {
            "predicted_result": (
                predicted_result
            ),
            "confidence": round(
                confidence,
                2,
            ),
            "margin": round(
                margin,
                2,
            ),
            "passes": passes,
        }

    @classmethod
    def passes(
        cls,
        prediction,
    ) -> bool:

        return bool(
            cls.details(
                prediction
            )["passes"]
        )

    @classmethod
    def sql_expression(
        cls,
        prediction_model,
    ):

        home_probability = (
            prediction_model
            .home_win_probability
        )

        draw_probability = (
            prediction_model
            .draw_probability
        )

        away_probability = (
            prediction_model
            .away_win_probability
        )

        home_passes = and_(
            home_probability
            >= cls.MINIMUM_CONFIDENCE,
            home_probability
            - draw_probability
            >= cls.MINIMUM_MARGIN,
            home_probability
            - away_probability
            >= cls.MINIMUM_MARGIN,
        )

        draw_passes = and_(
            draw_probability
            >= cls.MINIMUM_CONFIDENCE,
            draw_probability
            - home_probability
            >= cls.MINIMUM_MARGIN,
            draw_probability
            - away_probability
            >= cls.MINIMUM_MARGIN,
        )

        away_passes = and_(
            away_probability
            >= cls.MINIMUM_CONFIDENCE,
            away_probability
            - home_probability
            >= cls.MINIMUM_MARGIN,
            away_probability
            - draw_probability
            >= cls.MINIMUM_MARGIN,
        )

        return or_(
            home_passes,
            draw_passes,
            away_passes,
        )
