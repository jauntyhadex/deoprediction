from app.providers.base.sports_provider import SportsProvider


class FootballProvider(SportsProvider):
    """
    Football data provider.

    Initially this class will return sample data.
    Later it will connect to a real football API.
    """

    def get_competitions(self) -> list[dict]:
        return [
            {
                "id": 1,
                "name": "Premier League",
                "country": "England",
            },
            {
                "id": 2,
                "name": "La Liga",
                "country": "Spain",
            },
        ]

    def get_teams(self, competition_id: int) -> list[dict]:
        return []

    def get_players(self, team_id: int) -> list[dict]:
        return []

    def get_fixtures(self) -> list[dict]:
        return []