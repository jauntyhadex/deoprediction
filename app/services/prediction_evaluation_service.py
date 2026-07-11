from app.models.prediction_evaluation import (
    PredictionEvaluation,
)


class PredictionEvaluationService:

    def __init__(self, db):
        self.db = db

    def create_or_update(
        self,
        **kwargs,
    ):
        evaluation = (
            self.db.query(PredictionEvaluation)
            .filter(
                PredictionEvaluation.fixture_id
                == kwargs["fixture_id"]
            )
            .first()
        )

        if evaluation:
            for key, value in kwargs.items():
                setattr(
                    evaluation,
                    key,
                    value,
                )

            return evaluation

        evaluation = PredictionEvaluation(
            **kwargs
        )

        self.db.add(evaluation)

        return evaluation