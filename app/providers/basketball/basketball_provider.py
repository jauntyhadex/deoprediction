from app.providers.base.sports_provider import SportsProvider


class BasketballProvider(SportsProvider):
    """
    Basketball data provider.

    Initially this class will return sample data.
    Later it will connect to a real basketball API.
    """

    def get_competitions(self) -> list[dict]:
        return [
            {
                "id": 1,
                "name": "NBA",
                "country": "USA",
            },
            {
                "id": 2,
                "name": "EuroLeague",
                "country": "Europe",
            },
        ]

    def get_teams(self, competition_id: int) -> list[dict]:
        return []

    def get_players(self, team_id: int) -> list[dict]:
        return []

    def get_fixtures(self) -> list[dict]:
        return []