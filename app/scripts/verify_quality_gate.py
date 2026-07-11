from app.database import model_loader
from app.database.connection import SessionLocal
from app.models.prediction import Prediction
from app.models.prediction_pick import PredictionPick
from app.prediction.quality_gate import (
    PredictionQualityGate,
)


def main():

    db = SessionLocal()

    try:

        total_picks = (
            db.query(PredictionPick)
            .count()
        )

        invalid_picks = (
            db.query(PredictionPick)
            .join(
                Prediction,
                Prediction.fixture_id
                == PredictionPick.fixture_id,
            )
            .filter(
                Prediction.confidence
                < (
                    PredictionQualityGate
                    .MINIMUM_CONFIDENCE
                )
            )
            .count()
        )

        print(
            f"Minimum confidence: "
            f"{PredictionQualityGate.MINIMUM_CONFIDENCE}"
        )

        print(
            f"Total picks: "
            f"{total_picks}"
        )

        print(
            f"Invalid low-confidence picks: "
            f"{invalid_picks}"
        )

        if (
            total_picks > 0
            and invalid_picks == 0
        ):
            print(
                "\nQUALITY GATE VERIFICATION PASSED"
            )
        else:
            print(
                "\nQUALITY GATE VERIFICATION FAILED"
            )

            raise SystemExit(1)

    finally:

        db.close()


if __name__ == "__main__":
    main()