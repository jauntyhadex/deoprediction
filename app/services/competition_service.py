from sqlalchemy.orm import Session

from app.models.competition import Competition


class CompetitionService:
    def __init__(self, db: Session):
        self.db = db

    def get_by_external_id(self, external_id: int):
        return (
            self.db.query(Competition)
            .filter(Competition.external_id == external_id)
            .first()
        )

    def create(self, data: dict):
        existing = self.get_by_external_id(data["external_id"])

        if existing:
            return existing

        competition = Competition(**data)

        self.db.add(competition)
        self.db.commit()
        self.db.refresh(competition)

        return competition