from sqlalchemy.orm import Session

from app.models.strength_of_schedule import StrengthOfSchedule


class StrengthOfScheduleService:

    def __init__(self, db: Session):
        self.db = db

    def create_or_update(self, **kwargs):

        existing = (
            self.db.query(StrengthOfSchedule)
            .filter(
                StrengthOfSchedule.team_id == kwargs["team_id"]
            )
            .first()
        )

        if existing:

            for key, value in kwargs.items():
                setattr(existing, key, value)

            self.db.commit()
            self.db.refresh(existing)

            return existing

        sos = StrengthOfSchedule(**kwargs)

        self.db.add(sos)
        self.db.commit()
        self.db.refresh(sos)

        return sos