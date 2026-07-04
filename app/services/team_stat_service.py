from sqlalchemy.orm import Session

from app.models.team_stat import TeamStat


class TeamStatService:
    def __init__(self, db: Session):
        self.db = db

    def create_or_update(self, **kwargs):

        existing = (
            self.db.query(TeamStat)
            .filter(TeamStat.team_id == kwargs["team_id"])
            .first()
        )

        if existing:

            for key, value in kwargs.items():
                setattr(existing, key, value)

            self.db.commit()
            self.db.refresh(existing)

            return existing

        stat = TeamStat(**kwargs)

        self.db.add(stat)
        self.db.commit()
        self.db.refresh(stat)

        return stat