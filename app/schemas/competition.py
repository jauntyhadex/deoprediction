from pydantic import BaseModel


class CompetitionSchema(BaseModel):
    id: int
    name: str
    country: str
    sport: str