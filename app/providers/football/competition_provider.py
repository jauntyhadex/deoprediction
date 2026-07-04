from app.clients.football_api_client import FootballAPIClient
from app.enums import Sport


class CompetitionProvider:
    def __init__(self):
        self.client = FootballAPIClient()

    def fetch_competitions(self):
        data = self.client.get_competitions()

        competitions = []

        for competition in data["competitions"]:
            current_season = competition.get("currentSeason")

            season = ""
            if current_season:
                season = current_season["startDate"][:4]

            competitions.append(
                {
                    "external_id": competition["id"],
                    "code": competition["code"],
                    "name": competition["name"],
                    "country": competition["area"]["name"],
                    "type": competition["type"],
                    "emblem": competition.get("emblem"),
                    "season": season,
                    "sport": Sport.FOOTBALL,
                }
            )

        return competitions