from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import aliased

from app.models.fixture import Fixture
from app.models.prediction import Prediction
from app.models.prediction_market import (
    PredictionMarket,
)
from app.models.team import Team
from app.models.team_home_away_stats import (
    TeamHomeAwayStats,
)
from app.models.team_stat import TeamStat
from app.prediction.confidence import (
    ConfidenceCalculator,
)
from app.prediction.data_quality_gate import (
    PredictionDataQualityGate,
)
from app.prediction.quality_gate import (
    PredictionQualityGate,
)
from app.utils.datetime_utils import to_utc_iso
from app.services.competition_reliability_service import (
    CompetitionReliabilityService,
)


class PredictionMarketService:

    UPCOMING_STATUSES = [
        "SCHEDULED",
        "TIMED",
    ]

    def __init__(
        self,
        db,
    ):
        self.db = db

    @staticmethod
    def normalize_probability(
        probability: float,
    ) -> float:

        return round(
            max(
                0.0,
                min(
                    float(probability),
                    100.0,
                ),
            ),
            2,
        )

    @staticmethod
    def fair_odds(
        probability: float,
    ) -> float:

        probability = (
            PredictionMarketService
            .normalize_probability(
                probability
            )
        )

        if probability <= 0:
            return 0.0

        return round(
            100 / probability,
            2,
        )

    def create(
        self,
        **kwargs,
    ):

        probability = (
            self.normalize_probability(
                kwargs["probability"]
            )
        )

        market_type = (
            kwargs["market_type"]
        )

        kwargs["probability"] = (
            probability
        )

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

        market = PredictionMarket(
            **kwargs
        )

        self.db.add(
            market
        )

        return market

    def get_top_markets(
        self,
        limit: int = 20,
        upcoming_only: bool = True,
        days_ahead: int | None = 30,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        competition_id: int | None = None,
        competition_status: str | None = None,
        market_type: str | None = None,
        selection: str | None = None,
        minimum_fair_odds: float = 1.15,
        maximum_fair_odds: float = 8.0,
        minimum_probability: float = 0.0,
        minimum_market_confidence: float = 0.0,
        one_per_fixture: bool = True,
    ) -> list[dict]:

        reliability_service = (
            CompetitionReliabilityService(
                self.db
            )
        )

        reliability_reports = (
            reliability_service
            .get_reports_by_competition_id()
        )

        home_team = aliased(
            Team
        )

        away_team = aliased(
            Team
        )

        home_team_stat = aliased(
            TeamStat
        )

        away_team_stat = aliased(
            TeamStat
        )

        home_venue_stat = aliased(
            TeamHomeAwayStats
        )

        away_venue_stat = aliased(
            TeamHomeAwayStats
        )

        query = (
            self.db.query(
                PredictionMarket,
                Fixture,
                Prediction,
                home_team,
                away_team,
            )
            .join(
                Fixture,
                Fixture.id
                == PredictionMarket.fixture_id,
            )
            .join(
                Prediction,
                Prediction.fixture_id
                == Fixture.id,
            )
            .join(
                home_team,
                home_team.id
                == Fixture.home_team_id,
            )
            .join(
                away_team,
                away_team.id
                == Fixture.away_team_id,
            )
            .join(
                home_team_stat,
                home_team_stat.team_id
                == Fixture.home_team_id,
            )
            .join(
                away_team_stat,
                away_team_stat.team_id
                == Fixture.away_team_id,
            )
            .join(
                home_venue_stat,
                home_venue_stat.team_id
                == Fixture.home_team_id,
            )
            .join(
                away_venue_stat,
                away_venue_stat.team_id
                == Fixture.away_team_id,
            )
            .filter(
                PredictionQualityGate
                .sql_expression(
                    Prediction
                ),
                home_team_stat.matches_played
                >= (
                    PredictionDataQualityGate
                    .MINIMUM_TOTAL_MATCHES
                ),
                away_team_stat.matches_played
                >= (
                    PredictionDataQualityGate
                    .MINIMUM_TOTAL_MATCHES
                ),
                home_venue_stat.home_matches
                >= (
                    PredictionDataQualityGate
                    .MINIMUM_HOME_MATCHES
                ),
                away_venue_stat.away_matches
                >= (
                    PredictionDataQualityGate
                    .MINIMUM_AWAY_MATCHES
                ),
            )
        )

        if upcoming_only:

            now = datetime.now(UTC).replace(tzinfo=None)

            query = query.filter(
                Fixture.kickoff_time
                >= now,
                Fixture.status.in_(
                    self.UPCOMING_STATUSES
                ),
            )

            if days_ahead is not None:

                maximum_date = (
                    now
                    + timedelta(
                        days=days_ahead
                    )
                )

                query = query.filter(
                    Fixture.kickoff_time
                    <= maximum_date
                )

        if date_from is not None:

            query = query.filter(
                Fixture.kickoff_time
                >= date_from
            )

        if date_to is not None:

            query = query.filter(
                Fixture.kickoff_time
                <= date_to
            )

        if competition_id is not None:

            query = query.filter(
                Fixture.competition_id
                == competition_id
            )

        if competition_status:

            allowed_competition_ids = (
                reliability_service
                .get_competition_ids_for_status(
                    competition_status
                )
            )

            if not allowed_competition_ids:
                return []

            query = query.filter(
                Fixture.competition_id.in_(
                    allowed_competition_ids
                )
            )

        if market_type:

            query = query.filter(
                PredictionMarket.market_type
                == market_type.upper()
            )

        if selection:

            query = query.filter(
                PredictionMarket.selection
                == selection.upper()
            )

        query = query.filter(
            PredictionMarket.fair_odds
            >= minimum_fair_odds,
            PredictionMarket.fair_odds
            <= maximum_fair_odds,
            PredictionMarket.probability
            >= minimum_probability,
            PredictionMarket.confidence
            >= minimum_market_confidence,
        )

        query = query.order_by(
            PredictionMarket
            .confidence.desc(),
            PredictionMarket
            .probability.desc(),
            Fixture.kickoff_time.asc(),
        )

        if not one_per_fixture:

            rows = (
                query.limit(
                    limit
                )
                .all()
            )

            return [
                self._serialize_market(
                    market=market,
                    fixture=fixture,
                    prediction=prediction,
                    home_team=home,
                    away_team=away,
                    reliability_report=(
                        reliability_reports.get(
                            fixture.competition_id
                        )
                    ),
                )
                for (
                    market,
                    fixture,
                    prediction,
                    home,
                    away,
                ) in rows
            ]

        results = []
        used_fixture_ids = set()

        for (
            market,
            fixture,
            prediction,
            home,
            away,
        ) in query.yield_per(500):

            if (
                fixture.id
                in used_fixture_ids
            ):
                continue

            results.append(
                self._serialize_market(
                    market=market,
                    fixture=fixture,
                    prediction=prediction,
                    home_team=home,
                    away_team=away,
                    reliability_report=(
                        reliability_reports.get(
                            fixture.competition_id
                        )
                    ),
                )
            )

            used_fixture_ids.add(
                fixture.id
            )

            if len(results) >= limit:
                break

        return results

    @staticmethod
    def _serialize_market(
        market,
        fixture,
        prediction,
        home_team,
        away_team,
        reliability_report: dict | None,
    ) -> dict:

        probability = float(
            market.probability
        )

        confidence = float(
            market.confidence
        )

        score = (
            confidence * 0.70
            + probability * 0.30
        )

        score = max(
            0.0,
            min(
                score,
                100.0,
            ),
        )

        quality_details = (
            PredictionQualityGate.details(
                prediction
            )
        )

        reliability_report = (
            reliability_report
            or {
                "competition_name": None,
                "status": "UNVALIDATED",
                "status_message": (
                    "No walk-forward validation "
                    "evidence is currently available."
                ),
                "evaluations": 0,
                "accuracy": None,
                "brier": None,
            }
        )

        return {
            "market_id": market.id,
            "fixture_id": fixture.id,
            "competition_id": (
                fixture.competition_id
            ),
            "competition_name": (
                reliability_report[
                    "competition_name"
                ]
            ),
            "competition_status": (
                reliability_report[
                    "status"
                ]
            ),
            "competition_status_message": (
                reliability_report[
                    "status_message"
                ]
            ),
            "competition_evaluations": (
                reliability_report[
                    "evaluations"
                ]
            ),
            "competition_accuracy": (
                reliability_report[
                    "accuracy"
                ]
            ),
            "competition_brier": (
                reliability_report[
                    "brier"
                ]
            ),
            "kickoff_time": to_utc_iso(
                fixture.kickoff_time
            ),
            "status": fixture.status,
            "home_team": (
                home_team.name
            ),
            "away_team": (
                away_team.name
            ),
            "market_type": (
                market.market_type
            ),
            "selection": (
                market.selection
            ),
            "line": market.line,
            "probability": round(
                probability,
                2,
            ),
            "fair_odds": round(
                float(
                    market.fair_odds
                ),
                2,
            ),
            "market_confidence": round(
                confidence,
                2,
            ),
            "fixture_result": (
                quality_details[
                    "predicted_result"
                ]
            ),
            "fixture_confidence": (
                quality_details[
                    "confidence"
                ]
            ),
            "fixture_probability_margin": (
                quality_details[
                    "margin"
                ]
            ),
            "quality_gate": "PASSED",
            "data_quality": "SUFFICIENT",
            "score": round(
                score,
                2,
            ),
            "grade": (
                ConfidenceCalculator.grade(
                    confidence
                )
            ),
        }