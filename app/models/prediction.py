from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    fixture_id: Mapped[int] = mapped_column(
        ForeignKey("fixtures.id"),
        nullable=False,
    )

    home_win_probability: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    draw_probability: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    away_win_probability: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    predicted_home_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    predicted_away_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    fixture = relationship("Fixture")

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
    )