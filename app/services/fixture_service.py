from sqlalchemy.orm import Session

from app.models.fixture import Fixture


class FixtureService:
    def __init__(self, db: Session):
        self.db = db

    def get_by_external_id(self, external_id: int):
        return (
            self.db.query(Fixture)
            .filter(Fixture.api_fixture_id == external_id)
            .first()
        )

    def create(self, **kwargs):
        fixture = Fixture(**kwargs)

        self.db.add(fixture)
        self.db.commit()
        self.db.refresh(fixture)

        return fixture