from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class TeamPowerRating(Base):
    __tablename__ = "team_power_ratings"

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

    attack_power: Mapped[float] = mapped_column(
        Float,
        default=0,
    )

    defense_power: Mapped[float] = mapped_column(
        Float,
        default=0,
    )

    overall_power: Mapped[float] = mapped_column(
        Float,
        default=0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )