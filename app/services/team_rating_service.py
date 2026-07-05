from sqlalchemy.orm import Session

from app.models.team_rating import TeamRating


class TeamRatingService:

    def __init__(self, db: Session):
        self.db = db

    def create_or_update(self, **kwargs):

        existing = (
            self.db.query(TeamRating)
            .filter(
                TeamRating.team_id == kwargs["team_id"]
            )
            .first()
        )

        if existing:

            for key, value in kwargs.items():
                setattr(existing, key, value)

            self.db.commit()
            self.db.refresh(existing)

            return existing

        rating = TeamRating(**kwargs)

        self.db.add(rating)
        self.db.commit()
        self.db.refresh(rating)

        return rating