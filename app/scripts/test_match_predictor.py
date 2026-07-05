from app.database.connection import SessionLocal
from app.models.fixture import Fixture
from app.prediction.match_predictor import MatchPredictor


db = SessionLocal()

fixture = db.query(Fixture).first()

prediction = MatchPredictor.predict(
    db,
    fixture.home_team_id,
    fixture.away_team_id,
)

print(prediction)

db.close()