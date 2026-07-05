from sqlalchemy.orm import Session

from app.models.team_home_away_stats import TeamHomeAwayStats


class TeamHomeAwayStatsService:

    def __init__(self, db: Session):
        self.db = db

    def create_or_update(self, **kwargs):

        existing = (
            self.db.query(TeamHomeAwayStats)
            .filter(
                TeamHomeAwayStats.team_id == kwargs["team_id"]
            )
            .first()
        )

        if existing:

            for key, value in kwargs.items():
                setattr(existing, key, value)

            self.db.commit()
            self.db.refresh(existing)

            return existing

        stats = TeamHomeAwayStats(**kwargs)

        self.db.add(stats)
        self.db.commit()
        self.db.refresh(stats)

        return stats