from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.enums import Sport


class Competition(Base):
    __tablename__ = "competitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(100), nullable=False)

    country: Mapped[str] = mapped_column(String(100), nullable=False)

    season: Mapped[str] = mapped_column(String(20), nullable=False)

    sport: Mapped[Sport] = mapped_column(
        Enum(Sport),
        nullable=False,
    )

    teams = relationship(
        "Team",
        back_populates="competition",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )