from sqlalchemy.orm import Session

from app.models.team_form import TeamForm


class TeamFormService:
    def __init__(self, db: Session):
        self.db = db

    def create_or_update(self, **kwargs):

        existing = (
            self.db.query(TeamForm)
            .filter(TeamForm.team_id == kwargs["team_id"])
            .first()
        )

        if existing:

            for key, value in kwargs.items():
                setattr(existing, key, value)

            self.db.commit()
            self.db.refresh(existing)

            return existing

        form = TeamForm(**kwargs)

        self.db.add(form)
        self.db.commit()
        self.db.refresh(form)

        return form