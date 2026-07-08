from app.database import model_loader
from app.database.connection import SessionLocal
from app.services.prediction_pick_service import (
    PredictionPickService,
)


def main():

    db = SessionLocal()

    try:
        service = PredictionPickService(db)

        picks = service.get_top_picks(
            limit=20,
            minimum_grade="B",
        )

        print(f"Found {len(picks)} picks\n")

        for pick in picks:

            line_text = ""

            if pick["line"] is not None:
                line_text = f" {pick['line']:+g}"

            print(
                f"{pick['home_team']} vs "
                f"{pick['away_team']}"
            )

            print(
                f"Rank: {pick['rank']} | "
                f"Grade: {pick['grade']} | "
                f"Score: {pick['score']}"
            )

            print(
                f"{pick['market_type']} - "
                f"{pick['selection']}"
                f"{line_text}"
            )

            print(
                f"Probability: "
                f"{pick['probability']}% | "
                f"Fair odds: "
                f"{pick['fair_odds']}"
            )

            print("-" * 60)

    finally:
        db.close()


if __name__ == "__main__":
    main()