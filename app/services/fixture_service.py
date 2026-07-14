from datetime import UTC, datetime, timedelta

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, aliased

from app.models.competition import Competition
from app.models.fixture import Fixture
from app.models.team import Team


class FixtureService:

    UPCOMING_STATUSES = (
        "SCHEDULED",
        "TIMED",
        "POSTPONED",
        "SUSPENDED",
    )

    def __init__(
        self,
        db: Session,
    ) -> None:

        self.db = db

    def get_by_id(
        self,
        fixture_id: int,
    ):

        home_team = aliased(Team)
        away_team = aliased(Team)

        return (
            self.db.query(
                Fixture,
                Competition,
                home_team,
                away_team,
            )
            .join(
                Competition,
                Competition.id
                == Fixture.competition_id,
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
                Fixture.id == fixture_id
            )
            .first()
        )

    def get_by_external_id(
        self,
        external_id: int,
    ) -> Fixture | None:

        return (
            self.db.query(Fixture)
            .filter(
                Fixture.api_fixture_id
                == external_id
            )
            .first()
        )

    def list_catalog(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        upcoming_only: bool = True,
        days_ahead: int | None = 30,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        competition_id: int | None = None,
        team_id: int | None = None,
        status: str | None = None,
        search: str | None = None,
    ) -> tuple[int, list]:

        home_team = aliased(Team)
        away_team = aliased(Team)

        query = (
            self.db.query(
                Fixture,
                Competition,
                home_team,
                away_team,
            )
            .join(
                Competition,
                Competition.id
                == Fixture.competition_id,
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

        now = datetime.now(
            UTC
        ).replace(
            tzinfo=None
        )

        if upcoming_only:

            query = query.filter(
                Fixture.kickoff_time >= now,
                Fixture.status.in_(
                    self.UPCOMING_STATUSES
                ),
            )

            if (
                days_ahead is not None
                and date_to is None
            ):

                query = query.filter(
                    Fixture.kickoff_time
                    <= (
                        now
                        + timedelta(
                            days=days_ahead
                        )
                    )
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

        if team_id is not None:

            query = query.filter(
                or_(
                    Fixture.home_team_id
                    == team_id,
                    Fixture.away_team_id
                    == team_id,
                )
            )

        if status is not None:

            query = query.filter(
                Fixture.status == status
            )

        if search:

            search_pattern = (
                f"%{search.strip().lower()}%"
            )

            query = query.filter(
                or_(
                    func.lower(
                        home_team.name
                    ).like(search_pattern),
                    func.lower(
                        home_team.short_name
                    ).like(search_pattern),
                    func.lower(
                        home_team.tla
                    ).like(search_pattern),
                    func.lower(
                        away_team.name
                    ).like(search_pattern),
                    func.lower(
                        away_team.short_name
                    ).like(search_pattern),
                    func.lower(
                        away_team.tla
                    ).like(search_pattern),
                    func.lower(
                        Competition.name
                    ).like(search_pattern),
                    func.lower(
                        Competition.code
                    ).like(search_pattern),
                )
            )

        total = query.count()

        rows = (
            query.order_by(
                Fixture.kickoff_time.asc(),
                Fixture.id.asc(),
            )
            .offset(offset)
            .limit(limit)
            .all()
        )

        return total, rows

    def create(
        self,
        **kwargs,
    ) -> Fixture:

        fixture = Fixture(
            **kwargs
        )

        self.db.add(fixture)
        self.db.commit()
        self.db.refresh(fixture)

        return fixture
