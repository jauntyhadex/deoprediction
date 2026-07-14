from datetime import UTC, datetime

from sqlalchemy import insert

from app.database import model_loader
from app.database.connection import SessionLocal
from app.models.fixture import Fixture
from app.models.prediction_market import PredictionMarket
from app.prediction.expected_goals import (
    ExpectedGoalsCalculator,
)
from app.prediction.match_predictor import MatchPredictor
from app.prediction.confidence import (
    ConfidenceCalculator,
)
from app.prediction.probability import ProbabilityPredictor
from app.services.prediction_market_service import (
    PredictionMarketService,
)


class BulkPredictionMarketService:

    INSERT_BATCH_SIZE = 5_000

    def __init__(
        self,
        db,
    ) -> None:

        self.db = db
        self.rows: list[dict] = []
        self.created_count = 0
        self.created_at = datetime.now(UTC).replace(tzinfo=None)

    @staticmethod
    def fair_odds(
        probability: float,
    ) -> float:

        return (
            PredictionMarketService
            .fair_odds(
                probability
            )
        )

    def create(
        self,
        **kwargs,
    ) -> None:

        probability = (
            PredictionMarketService
            .normalize_probability(
                kwargs["probability"]
            )
        )

        market_type = kwargs[
            "market_type"
        ]

        kwargs["probability"] = probability

        kwargs["fair_odds"] = (
            self.fair_odds(
                probability
            )
        )

        kwargs["confidence"] = (
            ConfidenceCalculator.calculate(
                market_type,
                probability,
            )
        )

        kwargs["created_at"] = (
            self.created_at
        )

        self.rows.append(
            kwargs
        )

        if (
            len(self.rows)
            >= self.INSERT_BATCH_SIZE
        ):
            self.flush()

    def flush(self) -> None:

        if not self.rows:
            return

        self.db.execute(
            insert(
                PredictionMarket
            ),
            self.rows,
        )

        self.created_count += len(
            self.rows
        )

        self.rows.clear()


TOTAL_LINES = [
    0.5,
    1.5,
    2.5,
    3.5,
    4.5,
]

TEAM_TOTAL_LINES = [
    0.5,
    1.5,
    2.5,
]

ASIAN_HANDICAP_LINES = [
    -2.5,
    -1.5,
    -0.5,
    0.5,
    1.5,
    2.5,
]

PERIOD_TOTAL_LINES = [
    0.5,
    1.5,
    2.5,
]

PERIODS = [
    "FIRST_HALF",
    "SECOND_HALF",
]


def add_market(
    service,
    fixture_id,
    market_type,
    selection,
    probability,
    line=None,
):
    service.create(
        fixture_id=fixture_id,
        market_type=market_type,
        selection=selection,
        line=line,
        probability=round(probability, 2),
        fair_odds=service.fair_odds(probability),
        confidence=round(probability, 2),
    )


def generate_match_result_markets(
    service,
    fixture_id,
    prediction,
):
    add_market(
        service,
        fixture_id,
        "MATCH_RESULT",
        "HOME",
        prediction["home_win"],
    )

    add_market(
        service,
        fixture_id,
        "MATCH_RESULT",
        "DRAW",
        prediction["draw"],
    )

    add_market(
        service,
        fixture_id,
        "MATCH_RESULT",
        "AWAY",
        prediction["away_win"],
    )


def generate_btts_markets(
    service,
    fixture_id,
    btts_yes,
):
    add_market(
        service,
        fixture_id,
        "BTTS",
        "YES",
        btts_yes,
    )

    add_market(
        service,
        fixture_id,
        "BTTS",
        "NO",
        100 - btts_yes,
    )


def generate_double_chance_markets(
    service,
    fixture_id,
    home_xg,
    away_xg,
):
    probabilities = ProbabilityPredictor.double_chance(
        home_xg,
        away_xg,
    )

    add_market(
        service,
        fixture_id,
        "DOUBLE_CHANCE",
        "HOME_OR_DRAW",
        probabilities["home_or_draw"],
    )

    add_market(
        service,
        fixture_id,
        "DOUBLE_CHANCE",
        "HOME_OR_AWAY",
        probabilities["home_or_away"],
    )

    add_market(
        service,
        fixture_id,
        "DOUBLE_CHANCE",
        "DRAW_OR_AWAY",
        probabilities["draw_or_away"],
    )


def generate_draw_no_bet_markets(
    service,
    fixture_id,
    home_xg,
    away_xg,
):
    probabilities = ProbabilityPredictor.draw_no_bet(
        home_xg,
        away_xg,
    )

    add_market(
        service,
        fixture_id,
        "DRAW_NO_BET",
        "HOME",
        probabilities["home"],
    )

    add_market(
        service,
        fixture_id,
        "DRAW_NO_BET",
        "AWAY",
        probabilities["away"],
    )


def generate_total_goal_markets(
    service,
    fixture_id,
    home_xg,
    away_xg,
):
    for line in TOTAL_LINES:
        probabilities = ProbabilityPredictor.over_under(
            home_xg,
            away_xg,
            line,
        )

        add_market(
            service,
            fixture_id,
            "TOTAL_GOALS",
            "OVER",
            probabilities["over"],
            line=line,
        )

        add_market(
            service,
            fixture_id,
            "TOTAL_GOALS",
            "UNDER",
            probabilities["under"],
            line=line,
        )


def generate_team_total_markets(
    service,
    fixture_id,
    home_xg,
    away_xg,
):
    for line in TEAM_TOTAL_LINES:
        home_probabilities = ProbabilityPredictor.team_total(
            home_xg,
            line,
        )

        add_market(
            service,
            fixture_id,
            "HOME_TEAM_TOTAL",
            "OVER",
            home_probabilities["over"],
            line=line,
        )

        add_market(
            service,
            fixture_id,
            "HOME_TEAM_TOTAL",
            "UNDER",
            home_probabilities["under"],
            line=line,
        )

        away_probabilities = ProbabilityPredictor.team_total(
            away_xg,
            line,
        )

        add_market(
            service,
            fixture_id,
            "AWAY_TEAM_TOTAL",
            "OVER",
            away_probabilities["over"],
            line=line,
        )

        add_market(
            service,
            fixture_id,
            "AWAY_TEAM_TOTAL",
            "UNDER",
            away_probabilities["under"],
            line=line,
        )


def generate_clean_sheet_markets(
    service,
    fixture_id,
    home_xg,
    away_xg,
):
    probabilities = ProbabilityPredictor.clean_sheet(
        home_xg,
        away_xg,
    )

    add_market(
        service,
        fixture_id,
        "CLEAN_SHEET",
        "HOME",
        probabilities["home"],
    )

    add_market(
        service,
        fixture_id,
        "CLEAN_SHEET",
        "AWAY",
        probabilities["away"],
    )


def generate_win_to_nil_markets(
    service,
    fixture_id,
    home_xg,
    away_xg,
):
    probabilities = ProbabilityPredictor.win_to_nil(
        home_xg,
        away_xg,
    )

    add_market(
        service,
        fixture_id,
        "WIN_TO_NIL",
        "HOME",
        probabilities["home"],
    )

    add_market(
        service,
        fixture_id,
        "WIN_TO_NIL",
        "AWAY",
        probabilities["away"],
    )


def generate_asian_handicap_markets(
    service,
    fixture_id,
    home_xg,
    away_xg,
):
    for home_line in ASIAN_HANDICAP_LINES:
        probabilities = ProbabilityPredictor.asian_handicap(
            home_xg,
            away_xg,
            home_line,
        )

        add_market(
            service,
            fixture_id,
            "ASIAN_HANDICAP",
            "HOME",
            probabilities["home"],
            line=home_line,
        )

        add_market(
            service,
            fixture_id,
            "ASIAN_HANDICAP",
            "AWAY",
            probabilities["away"],
            line=-home_line,
        )


def generate_period_markets(
    service,
    fixture_id,
    home_xg,
    away_xg,
):
    for period in PERIODS:
        period_data = ProbabilityPredictor.period_probabilities(
            home_xg,
            away_xg,
            period,
        )

        add_market(
            service,
            fixture_id,
            f"{period}_RESULT",
            "HOME",
            period_data["home"],
        )

        add_market(
            service,
            fixture_id,
            f"{period}_RESULT",
            "DRAW",
            period_data["draw"],
        )

        add_market(
            service,
            fixture_id,
            f"{period}_RESULT",
            "AWAY",
            period_data["away"],
        )

        add_market(
            service,
            fixture_id,
            f"{period}_BTTS",
            "YES",
            period_data["btts_yes"],
        )

        add_market(
            service,
            fixture_id,
            f"{period}_BTTS",
            "NO",
            period_data["btts_no"],
        )

        for line in PERIOD_TOTAL_LINES:
            probabilities = ProbabilityPredictor.over_under(
                period_data["home_xg"],
                period_data["away_xg"],
                line,
            )

            add_market(
                service,
                fixture_id,
                f"{period}_TOTAL_GOALS",
                "OVER",
                probabilities["over"],
                line=line,
            )

            add_market(
                service,
                fixture_id,
                f"{period}_TOTAL_GOALS",
                "UNDER",
                probabilities["under"],
                line=line,
            )


def generate_correct_score_markets(
    service,
    fixture_id,
    home_xg,
    away_xg,
):
    scores = ProbabilityPredictor.correct_scores(
        home_xg,
        away_xg,
        top_n=5,
    )

    for score in scores:
        add_market(
            service,
            fixture_id,
            "CORRECT_SCORE",
            score["score"],
            score["probability"],
        )


def main():
    db = SessionLocal()
    service = BulkPredictionMarketService(db)

    try:
        db.query(PredictionMarket).delete(
            synchronize_session=False
        )

        fixtures = db.query(Fixture).all()
        total_fixtures = len(fixtures)

        prediction_data_cache = (
            ExpectedGoalsCalculator
            .build_cache(db)
        )

        print(
            f"Generating markets for "
            f"{total_fixtures} fixtures..."
        )

        for index, fixture in enumerate(
            fixtures,
            start=1,
        ):
            prediction = MatchPredictor.predict(
                db,
                fixture.home_team_id,
                fixture.away_team_id,
                data_cache=(
                    prediction_data_cache
                ),
            )

            home_xg = prediction["home_xg"]
            away_xg = prediction["away_xg"]

            generate_match_result_markets(
                service,
                fixture.id,
                prediction,
            )

            generate_btts_markets(
                service,
                fixture.id,
                prediction["btts"],
            )

            generate_double_chance_markets(
                service,
                fixture.id,
                home_xg,
                away_xg,
            )

            generate_draw_no_bet_markets(
                service,
                fixture.id,
                home_xg,
                away_xg,
            )

            generate_total_goal_markets(
                service,
                fixture.id,
                home_xg,
                away_xg,
            )

            generate_team_total_markets(
                service,
                fixture.id,
                home_xg,
                away_xg,
            )

            generate_clean_sheet_markets(
                service,
                fixture.id,
                home_xg,
                away_xg,
            )

            generate_win_to_nil_markets(
                service,
                fixture.id,
                home_xg,
                away_xg,
            )

            generate_asian_handicap_markets(
                service,
                fixture.id,
                home_xg,
                away_xg,
            )

            generate_period_markets(
                service,
                fixture.id,
                home_xg,
                away_xg,
            )

            generate_correct_score_markets(
                service,
                fixture.id,
                home_xg,
                away_xg,
            )

            if index % 100 == 0:

                print(
                    f"{index}/{total_fixtures} completed"
                )

        service.flush()

        db.commit()

        market_count = db.query(
            PredictionMarket
        ).count()

        print(f"Finished! {market_count} markets created.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()