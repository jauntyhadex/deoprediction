from app.clients.football_api_client import FootballAPIClient


class FixtureProvider:
    def __init__(self):
        self.client = FootballAPIClient()

    def get_matches(self, competition_code: str):
        data = self.client.get_matches(competition_code)

        return data.get("matches", [])