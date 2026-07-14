from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.competition import Competition


class CompetitionService:

    def __init__(
        self,
        db: Session,
    ) -> None:

        self.db = db

    def get_by_id(
        self,
        competition_id: int,
    ) -> Competition | None:

        return (
            self.db.query(Competition)
            .filter(
                Competition.id
                == competition_id
            )
            .first()
        )

    def get_by_external_id(
        self,
        external_id: int,
    ) -> Competition | None:

        return (
            self.db.query(Competition)
            .filter(
                Competition.external_id
                == external_id
            )
            .first()
        )

    def list_catalog(
        self,
        search: str | None = None,
        country: str | None = None,
    ) -> list[Competition]:

        query = self.db.query(
            Competition
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
                        Competition.name
                    ).like(
                        search_pattern
                    ),
                    func.lower(
                        Competition.code
                    ).like(
                        search_pattern
                    ),
                    func.lower(
                        Competition.country
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
                    Competition.country
                )
                == normalized_country
            )

        return (
            query.order_by(
                Competition.country.asc(),
                Competition.name.asc(),
            )
            .all()
        )

    def create(
        self,
        data: dict,
    ) -> Competition:

        existing = (
            self.get_by_external_id(
                data["external_id"]
            )
        )

        if existing:
            return existing

        competition = Competition(
            **data
        )

        self.db.add(competition)
        self.db.commit()
        self.db.refresh(competition)

        return competition
