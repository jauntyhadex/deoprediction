from app.clients.football_api_client import FootballAPIClient


class TeamProvider:
    def __init__(self):
        self.client = FootballAPIClient()

    def get_teams(self, competition_code: str):
        data = self.client.get_teams(competition_code)

        return data.get("teams", [])