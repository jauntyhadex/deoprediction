from sqlalchemy.orm import aliased

from app.models.fixture import Fixture
from app.models.prediction_market import PredictionMarket
from app.models.prediction_pick import PredictionPick
from app.models.team import Team


class PredictionPickService:

    def __init__(self, db):
        self.db = db

    def get_fixture_picks(
        self,
        fixture_id: int,
        limit: int = 5,
    ) -> list[dict]:

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
                pick,
                market,
                fixture,
                home,
                away,
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
    ) -> list[dict]:

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

        if minimum_grade:
            allowed_grades = self._allowed_grades(
                minimum_grade
            )

            query = query.filter(
                PredictionPick.grade.in_(
                    allowed_grades
                )
            )

        rows = (
            query.order_by(
                PredictionPick.score.desc(),
                PredictionMarket.probability.desc(),
            )
            .limit(limit)
            .all()
        )

        return [
            self._serialize(
                pick,
                market,
                fixture,
                home,
                away,
            )
            for (
                pick,
                market,
                fixture,
                home,
                away,
            ) in rows
        ]

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

        index = grades.index(minimum_grade)

        return grades[: index + 1]

    @staticmethod
    def _serialize(
        pick,
        market,
        fixture,
        home_team,
        away_team,
    ) -> dict:

        return {
            "pick_id": pick.id,
            "fixture_id": fixture.id,
            "kickoff_time": fixture.kickoff_time,
            "status": fixture.status,
            "home_team": home_team.name,
            "away_team": away_team.name,
            "rank": pick.rank,
            "score": round(pick.score, 2),
            "grade": pick.grade,
            "market_type": market.market_type,
            "selection": market.selection,
            "line": market.line,
            "probability": round(
                market.probability,
                2,
            ),
            "fair_odds": round(
                market.fair_odds,
                2,
            ),
            "confidence": round(
                market.confidence,
                2,
            ),
        }