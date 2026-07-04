from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class TeamStat(Base):
    __tablename__ = "team_stats"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id"),
        nullable=False,
        unique=True,
    )

    matches_played: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    wins: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    draws: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    losses: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    goals_for: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    goals_against: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    goal_difference: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    points: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    win_rate: Mapped[float] = mapped_column(
        Float,
        default=0,
    )

    draw_rate: Mapped[float] = mapped_column(
        Float,
        default=0,
    )

    loss_rate: Mapped[float] = mapped_column(
        Float,
        default=0,
    )

    team = relationship("Team")

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )