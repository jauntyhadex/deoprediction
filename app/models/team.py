from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Football-data.org ID
    external_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    short_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    tla: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )

    country: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    founded: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    venue: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    website: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    club_colors: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    logo: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    competition_id: Mapped[int] = mapped_column(
        ForeignKey("competitions.id"),
        nullable=False,
    )

    competition = relationship(
        "Competition",
        back_populates="teams",
    )

    players = relationship(
        "Player",
        back_populates="team",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
    )