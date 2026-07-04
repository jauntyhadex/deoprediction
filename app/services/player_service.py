from sqlalchemy.orm import Session

from app.models.player import Player


class PlayerService:
    def __init__(self, db: Session):
        self.db = db

    def get_by_external_id(self, external_id: int):
        return (
            self.db.query(Player)
            .filter(Player.external_id == external_id)
            .first()
        )

    def create(
        self,
        external_id: int,
        name: str,
        jersey_number: int | None,
        position: str,
        nationality: str | None,
        date_of_birth,
        team_id: int,
    ):
        player = Player(
            external_id=external_id,
            name=name,
            jersey_number=jersey_number,
            position=position,
            nationality=nationality,
            date_of_birth=date_of_birth,
            team_id=team_id,
        )

        self.db.add(player)
        self.db.commit()
        self.db.refresh(player)

        return player