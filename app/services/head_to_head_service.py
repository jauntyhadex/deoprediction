from sqlalchemy.orm import Session

from app.models.head_to_head import HeadToHead


class HeadToHeadService:

    def __init__(self, db: Session):
        self.db = db

    def create_or_update(self, **kwargs):

        existing = (
            self.db.query(HeadToHead)
            .filter(
                HeadToHead.home_team_id == kwargs["home_team_id"],
                HeadToHead.away_team_id == kwargs["away_team_id"],
            )
            .first()
        )

        if existing:

            for key, value in kwargs.items():
                setattr(existing, key, value)

            self.db.commit()
            self.db.refresh(existing)

            return existing

        h2h = HeadToHead(**kwargs)

        self.db.add(h2h)
        self.db.commit()
        self.db.refresh(h2h)

        return h2h