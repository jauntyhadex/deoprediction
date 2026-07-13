from app.database import model_loader
from app.database.connection import (
    SessionLocal,
)
from app.models.prediction import Prediction
from app.models.prediction_pick import (
    PredictionPick,
)
from app.prediction.quality_gate import (
    PredictionQualityGate,
)


def main():

    db = SessionLocal()

    try:

        rows = (
            db.query(
                PredictionPick,
                Prediction,
            )
            .join(
                Prediction,
                Prediction.fixture_id
                == PredictionPick.fixture_id,
            )
            .order_by(
                PredictionPick.id.asc()
            )
            .all()
        )

        total_picks = len(
            rows
        )

        invalid_picks = 0
        low_confidence_picks = 0
        low_margin_picks = 0

        invalid_fixture_ids = set()

        for pick, prediction in rows:

            details = (
                PredictionQualityGate.details(
                    prediction
                )
            )

            confidence_passes = (
                details["confidence"]
                >= (
                    PredictionQualityGate
                    .MINIMUM_CONFIDENCE
                )
            )

            margin_passes = (
                details["margin"]
                >= (
                    PredictionQualityGate
                    .MINIMUM_MARGIN
                )
            )

            if not confidence_passes:
                low_confidence_picks += 1

            if not margin_passes:
                low_margin_picks += 1

            if not details["passes"]:

                invalid_picks += 1

                invalid_fixture_ids.add(
                    pick.fixture_id
                )

        print(
            "\nQUALITY GATE VERIFICATION"
        )

        print("-" * 60)

        print(
            "Minimum confidence: "
            f"{PredictionQualityGate.MINIMUM_CONFIDENCE}"
        )

        print(
            "Minimum probability margin: "
            f"{PredictionQualityGate.MINIMUM_MARGIN}"
        )

        print(
            f"Total picks: "
            f"{total_picks}"
        )

        print(
            "Low-confidence picks: "
            f"{low_confidence_picks}"
        )

        print(
            "Low-margin picks: "
            f"{low_margin_picks}"
        )

        print(
            "Invalid picks: "
            f"{invalid_picks}"
        )

        print(
            "Invalid fixtures: "
            f"{len(invalid_fixture_ids)}"
        )

        if (
            total_picks > 0
            and invalid_picks == 0
        ):

            print()
            print(
                "QUALITY GATE "
                "VERIFICATION PASSED"
            )

        else:

            print()
            print(
                "QUALITY GATE "
                "VERIFICATION FAILED"
            )

            raise SystemExit(1)

    finally:

        db.close()


if __name__ == "__main__":
    main()