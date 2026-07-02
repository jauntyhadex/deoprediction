from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Fixture(Base):
    __tablename__ = "fixtures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    api_fixture_id: Mapped[int | None] = mapped_column(
        Integer,
        unique=True,
        nullable=True,
    )

    competition_id: Mapped[int] = mapped_column(
        ForeignKey("competitions.id"),
        nullable=False,
    )

    home_team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id"),
        nullable=False,
    )

    away_team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id"),
        nullable=False,
    )

    season: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    venue: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="Scheduled",
    )

    kickoff_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    home_score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    away_score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    competition = relationship("Competition")

    home_team = relationship(
        "Team",
        foreign_keys=[home_team_id],
    )

    away_team = relationship(
        "Team",
        foreign_keys=[away_team_id],
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )