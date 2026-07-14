from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.competition import Competition
from app.models.team import Team


class TeamService:

    def __init__(
        self,
        db: Session,
    ) -> None:

        self.db = db

    def get_by_id(
        self,
        team_id: int,
    ):

        return (
            self.db.query(
                Team,
                Competition,
            )
            .join(
                Competition,
                Competition.id
                == Team.competition_id,
            )
            .filter(
                Team.id == team_id
            )
            .first()
        )

    def get_by_external_id(
        self,
        external_id: int,
    ) -> Team | None:

        return (
            self.db.query(Team)
            .filter(
                Team.external_id
                == external_id
            )
            .first()
        )

    def list_catalog(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        search: str | None = None,
        country: str | None = None,
        competition_id: int | None = None,
    ) -> tuple[int, list]:

        query = (
            self.db.query(
                Team,
                Competition,
            )
            .join(
                Competition,
                Competition.id
                == Team.competition_id,
            )
        )

        if search:

            normalized_search = (
                search.strip().lower()
            )

            search_pattern = (
                f"%{normalized_search}%"
            )

            query = query.filter(
                or_(
                    func.lower(
                        Team.name
                    ).like(
                        search_pattern
                    ),
                    func.lower(
                        Team.short_name
                    ).like(
                        search_pattern
                    ),
                    func.lower(
                        Team.tla
                    ).like(
                        search_pattern
                    ),
                    func.lower(
                        Team.venue
                    ).like(
                        search_pattern
                    ),
                    func.lower(
                        Competition.name
                    ).like(
                        search_pattern
                    ),
                    func.lower(
                        Competition.code
                    ).like(
                        search_pattern
                    ),
                )
            )

        if country:

            normalized_country = (
                country.strip().lower()
            )

            query = query.filter(
                func.lower(
                    Team.country
                )
                == normalized_country
            )

        if competition_id is not None:

            query = query.filter(
                Team.competition_id
                == competition_id
            )

        total = query.count()

        rows = (
            query.order_by(
                Team.country.asc(),
                Team.name.asc(),
                Team.id.asc(),
            )
            .offset(offset)
            .limit(limit)
            .all()
        )

        return total, rows

    def create(
        self,
        **kwargs,
    ) -> Team:

        team = Team(
            **kwargs
        )

        self.db.add(team)
        self.db.commit()
        self.db.refresh(team)

        return team
