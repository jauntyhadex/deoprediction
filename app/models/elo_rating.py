from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class EloRating(Base):
    __tablename__ = "elo_ratings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id"),
        unique=True,
        nullable=False,
    )

    elo_rating: Mapped[float] = mapped_column(
        Float,
        default=1500,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
    )