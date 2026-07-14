from datetime import UTC, datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)

from app.database.base import Base


class PredictionPick(Base):

    __tablename__ = "prediction_picks"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    fixture_id = Column(
        Integer,
        ForeignKey("fixtures.id"),
        nullable=False,
        index=True,
    )

    market_id = Column(
        Integer,
        ForeignKey("prediction_markets.id"),
        nullable=False,
        unique=True,
    )

    rank = Column(
        Integer,
        nullable=False,
    )

    score = Column(
        Float,
        nullable=False,
    )

    grade = Column(
        String,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "fixture_id",
            "rank",
            name="uq_prediction_pick_fixture_rank",
        ),
    )