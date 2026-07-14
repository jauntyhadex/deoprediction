from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class TeamRating(Base):
    __tablename__ = "team_ratings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id"),
        unique=True,
        nullable=False,
    )

    attack_rating: Mapped[float] = mapped_column(
        Float,
        default=0,
    )

    defense_rating: Mapped[float] = mapped_column(
        Float,
        default=0,
    )

    overall_rating: Mapped[float] = mapped_column(
        Float,
        default=0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
    )