from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String

from app.database.base import Base


class PredictionMarket(Base):

    __tablename__ = "prediction_markets"

    id = Column(Integer, primary_key=True, index=True)

    fixture_id = Column(
        Integer,
        ForeignKey("fixtures.id"),
        nullable=False,
    )

    market_type = Column(String, nullable=False)
    selection = Column(String, nullable=False)

    line = Column(Float, nullable=True)

    probability = Column(Float, nullable=False)
    fair_odds = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )