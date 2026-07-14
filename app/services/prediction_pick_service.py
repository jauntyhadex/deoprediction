from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import aliased

from app.models.fixture import Fixture
from app.models.prediction_market import (
    PredictionMarket,
)
from app.models.prediction_pick import (
    PredictionPick,
)
from app.models.team import Team
from app.utils.datetime_utils import to_utc_iso
from app.services.competition_reliability_service import (
    CompetitionReliabilityService,
)


class PredictionPickService:

    UPCOMING_STATUSES = [
        "SCHEDULED",
        "TIMED",
    ]

    def __init__(self, db):
        self.db = db

    def get_fixture_picks(
        self,
        fixture_id: int,
        limit: int = 5,
    ) -> list[dict]:

        reliability_reports = (
            CompetitionReliabilityService(
                self.db
            )
            .get_reports_by_competition_id()
        )

        home_team = aliased(Team)
        away_team = aliased(Team)

        rows = (
            self.db.query(
                PredictionPick,
                PredictionMarket,
                Fixture,
                home_team,
                away_team,
            )
            .join(
                PredictionMarket,
                PredictionMarket.id
                == PredictionPick.market_id,
            )
            .join(
                Fixture,
                Fixture.id
                == PredictionPick.fixture_id,
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
            .filter(
                PredictionPick.fixture_id
                == fixture_id
            )
            .order_by(
                PredictionPick.rank.asc()
            )
            .limit(limit)
            .all()
        )

        return [
            self._serialize(
                pick=pick,
                market=market,
                fixture=fixture,
                home_team=home,
                away_team=away,
                reliability_report=(
                    reliability_reports.get(
                        fixture.competition_id
                    )
                ),
            )
            for (
                pick,
                market,
                fixture,
                home,
                away,
            ) in rows
        ]

    def get_top_picks(
        self,
        limit: int = 20,
        minimum_grade: str | None = None,
        upcoming_only: bool = True,
        days_ahead: int | None = 30,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        competition_id: int | None = None,
        competition_status: str | None = None,
        market_type: str | None = None,
        minimum_fair_odds: float = 1.15,
        maximum_fair_odds: float = 8.0,
        minimum_probability: float = 0.0,
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

        home_team = aliased(Team)
        away_team = aliased(Team)

        query = (
            self.db.query(
                PredictionPick,
                PredictionMarket,
                Fixture,
                home_team,
                away_team,
            )
            .join(
                PredictionMarket,
                PredictionMarket.id
                == PredictionPick.market_id,
            )
            .join(
                Fixture,
                Fixture.id
                == PredictionPick.fixture_id,
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
        )

        if upcoming_only:

            now = datetime.now(UTC).replace(tzinfo=None)

            query = query.filter(
                Fixture.kickoff_time >= now,
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

        query = query.filter(
            PredictionMarket.fair_odds
            >= minimum_fair_odds,
            PredictionMarket.fair_odds
            <= maximum_fair_odds,
            PredictionMarket.probability
            >= minimum_probability,
        )

        if minimum_grade:

            query = query.filter(
                PredictionPick.grade.in_(
                    self._allowed_grades(
                        minimum_grade
                    )
                )
            )

        query = query.order_by(
            PredictionPick.score.desc(),
            PredictionMarket.probability.desc(),
            Fixture.kickoff_time.asc(),
        )

        if not one_per_fixture:

            rows = query.limit(limit).all()

            return [
                self._serialize(
                    pick=pick,
                    market=market,
                    fixture=fixture,
                    home_team=home,
                    away_team=away,
                    reliability_report=(
                        reliability_reports.get(
                            fixture.competition_id
                        )
                    ),
                )
                for (
                    pick,
                    market,
                    fixture,
                    home,
                    away,
                ) in rows
            ]

        results = []
        used_fixture_ids = set()

        for (
            pick,
            market,
            fixture,
            home,
            away,
        ) in query.yield_per(500):

            if fixture.id in used_fixture_ids:
                continue

            results.append(
                self._serialize(
                    pick=pick,
                    market=market,
                    fixture=fixture,
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
    def _allowed_grades(
        minimum_grade: str,
    ) -> list[str]:

        grades = [
            "A+",
            "A",
            "B",
            "C",
            "D",
            "E",
        ]

        minimum_grade = minimum_grade.upper()

        if minimum_grade not in grades:
            return grades

        index = grades.index(
            minimum_grade
        )

        return grades[: index + 1]

    @staticmethod
    def _serialize(
        pick,
        market,
        fixture,
        home_team,
        away_team,
        reliability_report: dict | None,
    ) -> dict:

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
            "pick_id": pick.id,
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
                reliability_report["status"]
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
                reliability_report["accuracy"]
            ),
            "competition_brier": (
                reliability_report["brier"]
            ),
            "kickoff_time": to_utc_iso(
                fixture.kickoff_time
            ),
            "status": fixture.status,
            "home_team": home_team.name,
            "away_team": away_team.name,
            "rank": pick.rank,
            "score": round(
                float(pick.score),
                2,
            ),
            "grade": pick.grade,
            "market_type": (
                market.market_type
            ),
            "selection": market.selection,
            "line": market.line,
            "probability": round(
                float(market.probability),
                2,
            ),
            "fair_odds": round(
                float(market.fair_odds),
                2,
            ),
            "confidence": round(
                float(market.confidence),
                2,
            ),
        }