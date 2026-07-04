import httpx

from app.config.settings import settings


class FootballAPIClient:
    def __init__(self):
        self.base_url = settings.football_data_base_url
        self.headers = {
            "X-Auth-Token": settings.football_data_api_key
        }

    def get_competitions(self):
        response = httpx.get(
            f"{self.base_url}/competitions",
            headers=self.headers,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def get_teams(self, competition_code: str):
        response = httpx.get(
            f"{self.base_url}/competitions/{competition_code}/teams",
            headers=self.headers,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def get_matches(self, competition_code: str):
        response = httpx.get(
            f"{self.base_url}/competitions/{competition_code}/matches",
            headers=self.headers,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()