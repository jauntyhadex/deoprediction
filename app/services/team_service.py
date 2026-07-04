from sqlalchemy.orm import Session

from app.models.team import Team


class TeamService:
    def __init__(self, db: Session):
        self.db = db

    def get_by_external_id(self, external_id: int):
        return (
            self.db.query(Team)
            .filter(Team.external_id == external_id)
            .first()
        )

    def create(self, **kwargs):
        team = Team(**kwargs)

        self.db.add(team)
        self.db.commit()
        self.db.refresh(team)

        return team