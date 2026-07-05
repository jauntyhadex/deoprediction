from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class HeadToHead(Base):
    __tablename__ = "head_to_head"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    home_team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id"),
        nullable=False,
    )

    away_team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id"),
        nullable=False,
    )

    matches_played: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    home_wins: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    draws: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    away_wins: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    home_goals: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    away_goals: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    average_goals: Mapped[float] = mapped_column(
        Float,
        default=0,
    )

    btts_rate: Mapped[float] = mapped_column(
        Float,
        default=0,
    )

    over25_rate: Mapped[float] = mapped_column(
        Float,
        default=0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )