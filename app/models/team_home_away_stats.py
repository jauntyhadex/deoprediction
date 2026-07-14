from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class TeamHomeAwayStats(Base):
    __tablename__ = "team_home_away_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id"),
        unique=True,
    )

    home_matches = mapped_column(Integer, default=0)
    home_wins = mapped_column(Integer, default=0)
    home_draws = mapped_column(Integer, default=0)
    home_losses = mapped_column(Integer, default=0)
    home_goals_for = mapped_column(Integer, default=0)
    home_goals_against = mapped_column(Integer, default=0)

    away_matches = mapped_column(Integer, default=0)
    away_wins = mapped_column(Integer, default=0)
    away_draws = mapped_column(Integer, default=0)
    away_losses = mapped_column(Integer, default=0)
    away_goals_for = mapped_column(Integer, default=0)
    away_goals_against = mapped_column(Integer, default=0)

    home_win_rate = mapped_column(Float, default=0)
    away_win_rate = mapped_column(Float, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
    )

    team = relationship("Team")