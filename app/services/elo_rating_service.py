from sqlalchemy.orm import Session

from app.models.elo_rating import EloRating


class EloRatingService:

    def __init__(self, db: Session):
        self.db = db

    def create_or_update(self, **kwargs):

        existing = (
            self.db.query(EloRating)
            .filter(EloRating.team_id == kwargs["team_id"])
            .first()
        )

        if existing:

            for key, value in kwargs.items():
                setattr(existing, key, value)

            self.db.commit()
            self.db.refresh(existing)

            return existing

        rating = EloRating(**kwargs)

        self.db.add(rating)
        self.db.commit()
        self.db.refresh(rating)

        return rating