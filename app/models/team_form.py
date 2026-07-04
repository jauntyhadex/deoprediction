from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class TeamForm(Base):
    __tablename__ = "team_forms"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id"),
        unique=True,
        nullable=False,
    )

    last_five: Mapped[str] = mapped_column(
        String(5),
        default="",
    )

    last_ten_points: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    current_win_streak: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    current_unbeaten_streak: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    team = relationship("Team")