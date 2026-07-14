from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)

from app.database.base import Base


class PredictionEvaluation(Base):

    __tablename__ = "prediction_evaluations"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    fixture_id = Column(
        Integer,
        ForeignKey("fixtures.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    prediction_id = Column(
        Integer,
        ForeignKey("predictions.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    predicted_result = Column(
        String,
        nullable=False,
    )

    actual_result = Column(
        String,
        nullable=False,
    )

    result_correct = Column(
        Boolean,
        nullable=False,
    )

    predicted_home_score = Column(
        Integer,
        nullable=False,
    )

    predicted_away_score = Column(
        Integer,
        nullable=False,
    )

    actual_home_score = Column(
        Integer,
        nullable=False,
    )

    actual_away_score = Column(
        Integer,
        nullable=False,
    )

    score_correct = Column(
        Boolean,
        nullable=False,
    )

    home_win_probability = Column(
        Float,
        nullable=False,
    )

    draw_probability = Column(
        Float,
        nullable=False,
    )

    away_win_probability = Column(
        Float,
        nullable=False,
    )

    confidence = Column(
        Float,
        nullable=False,
    )

    brier_score = Column(
        Float,
        nullable=False,
    )

    goal_error = Column(
        Float,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
        nullable=False,
    )

    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
        onupdate=lambda: datetime.now(UTC).replace(tzinfo=None),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "fixture_id",
            name="uq_prediction_evaluation_fixture",
        ),
    )