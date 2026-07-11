from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)

from app.database.base import Base


class WalkForwardEvaluation(Base):

    __tablename__ = "walk_forward_evaluations"

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

    competition_id = Column(
        Integer,
        ForeignKey("competitions.id"),
        nullable=False,
        index=True,
    )

    home_team_id = Column(
        Integer,
        ForeignKey("teams.id"),
        nullable=False,
        index=True,
    )

    away_team_id = Column(
        Integer,
        ForeignKey("teams.id"),
        nullable=False,
        index=True,
    )

    kickoff_time = Column(
        DateTime,
        nullable=False,
        index=True,
    )

    home_history_matches = Column(
        Integer,
        nullable=False,
    )

    away_history_matches = Column(
        Integer,
        nullable=False,
    )

    home_xg = Column(
        Float,
        nullable=False,
    )

    away_xg = Column(
        Float,
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

    brier_score = Column(
        Float,
        nullable=False,
    )

    log_loss = Column(
        Float,
        nullable=False,
    )

    goal_error = Column(
        Float,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )