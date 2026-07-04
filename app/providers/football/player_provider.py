from app.clients.football_api_client import FootballAPIClient


class PlayerProvider:
    def __init__(self):
        self.client = FootballAPIClient()

    def get_players(self, team_id: int):
        data = self.client.get_players(team_id)

        return data.get("squad", [])