from app.database import model_loader
from app.database.connection import SessionLocal
from app.models.fixture import Fixture
from app.models.prediction import Prediction
from app.models.prediction_evaluation import (
    PredictionEvaluation,
)
from app.services.prediction_evaluation_service import (
    PredictionEvaluationService,
)


def get_result(
    home_score: int,
    away_score: int,
) -> str:

    if home_score > away_score:
        return "HOME"

    if home_score < away_score:
        return "AWAY"

    return "DRAW"


def get_predicted_result(
    prediction,
) -> str:

    probabilities = {
        "HOME": float(
            prediction.home_win_probability
        ),
        "DRAW": float(
            prediction.draw_probability
        ),
        "AWAY": float(
            prediction.away_win_probability
        ),
    }

    return max(
        probabilities,
        key=probabilities.get,
    )


def calculate_brier_score(
    prediction,
    actual_result: str,
) -> float:

    home_probability = (
        float(
            prediction.home_win_probability
        )
        / 100
    )

    draw_probability = (
        float(
            prediction.draw_probability
        )
        / 100
    )

    away_probability = (
        float(
            prediction.away_win_probability
        )
        / 100
    )

    actual_home = (
        1.0
        if actual_result == "HOME"
        else 0.0
    )

    actual_draw = (
        1.0
        if actual_result == "DRAW"
        else 0.0
    )

    actual_away = (
        1.0
        if actual_result == "AWAY"
        else 0.0
    )

    score = (
        (
            home_probability
            - actual_home
        ) ** 2
        + (
            draw_probability
            - actual_draw
        ) ** 2
        + (
            away_probability
            - actual_away
        ) ** 2
    ) / 3

    return round(score, 4)


def calculate_goal_error(
    prediction,
    fixture,
) -> float:

    home_error = abs(
        int(
            prediction.predicted_home_score
        )
        - int(fixture.home_score)
    )

    away_error = abs(
        int(
            prediction.predicted_away_score
        )
        - int(fixture.away_score)
    )

    return round(
        (
            home_error
            + away_error
        ) / 2,
        2,
    )


def main():

    db = SessionLocal()

    service = PredictionEvaluationService(
        db
    )

    try:
        fixtures = (
            db.query(Fixture)
            .filter(
                Fixture.home_score.isnot(None),
                Fixture.away_score.isnot(None),
            )
            .all()
        )

        total_fixtures = len(fixtures)

        print(
            f"Backtesting "
            f"{total_fixtures} fixtures..."
        )

        processed = 0
        skipped = 0

        for index, fixture in enumerate(
            fixtures,
            start=1,
        ):
            prediction = (
                db.query(Prediction)
                .filter(
                    Prediction.fixture_id
                    == fixture.id
                )
                .first()
            )

            if not prediction:
                skipped += 1
                continue

            actual_result = get_result(
                fixture.home_score,
                fixture.away_score,
            )

            predicted_result = (
                get_predicted_result(
                    prediction
                )
            )

            service.create_or_update(
                fixture_id=fixture.id,
                prediction_id=prediction.id,
                predicted_result=predicted_result,
                actual_result=actual_result,
                result_correct=(
                    predicted_result
                    == actual_result
                ),
                predicted_home_score=int(
                    prediction.predicted_home_score
                ),
                predicted_away_score=int(
                    prediction.predicted_away_score
                ),
                actual_home_score=int(
                    fixture.home_score
                ),
                actual_away_score=int(
                    fixture.away_score
                ),
                score_correct=(
                    int(
                        prediction
                        .predicted_home_score
                    )
                    == int(fixture.home_score)
                    and int(
                        prediction
                        .predicted_away_score
                    )
                    == int(fixture.away_score)
                ),
                home_win_probability=float(
                    prediction
                    .home_win_probability
                ),
                draw_probability=float(
                    prediction.draw_probability
                ),
                away_win_probability=float(
                    prediction
                    .away_win_probability
                ),
                confidence=float(
                    prediction.confidence
                ),
                brier_score=(
                    calculate_brier_score(
                        prediction,
                        actual_result,
                    )
                ),
                goal_error=(
                    calculate_goal_error(
                        prediction,
                        fixture,
                    )
                ),
            )

            processed += 1

            if index % 100 == 0:
                db.commit()

                print(
                    f"{index}/"
                    f"{total_fixtures} completed"
                )

        db.commit()

        evaluation_count = (
            db.query(
                PredictionEvaluation
            )
            .count()
        )

        print(
            f"Finished! "
            f"{processed} processed, "
            f"{skipped} skipped."
        )

        print(
            f"Prediction evaluations: "
            f"{evaluation_count}"
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()