from sqlalchemy.orm import Session

from app.models.prediction import Prediction


class PredictionService:
    def __init__(self, db: Session):
        self.db = db

    def get_by_fixture(self, fixture_id: int):
        return (
            self.db.query(Prediction)
            .filter(Prediction.fixture_id == fixture_id)
            .first()
        )

    def create(self, **kwargs):
        prediction = Prediction(**kwargs)

        self.db.add(prediction)
        self.db.commit()
        self.db.refresh(prediction)

        return prediction