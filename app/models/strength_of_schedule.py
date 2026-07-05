from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class StrengthOfSchedule(Base):
    __tablename__ = "strength_of_schedule"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id"),
        unique=True,
        nullable=False,
    )

    sos_rating: Mapped[float] = mapped_column(
        Float,
        default=0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )